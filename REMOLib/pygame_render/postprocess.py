"""Utility classes for building GLSL based post-processing pipelines.

This module provides a small framework that makes it straightforward to
chain multiple full-screen shader passes on top of REMO's ModernGL
rendering backend.  The pipeline is designed to be lightweight and to
cover the most common use cases (bloom, CRT simulation and basic colour
grading) while still remaining fully extensible.

Typical usage::

    Rs.postprocess.use(
        Rs.postprocess.bloom(intensity=1.35),
        Rs.postprocess.crt(),
        Rs.postprocess.color_grade(saturation=1.1)
    )

The pipeline renders the intermediate passes to two internal ping-pong
framebuffers and returns the resulting texture which can then be
composited to the main display.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from typing import Callable, Dict, List, Optional

import pygame

from .engine import RenderEngine
from .layer import Layer
from .shader import Shader
from moderngl import Texture


def _read_shader_source(filename: str) -> str:
    """Load a GLSL file bundled with the pygame_render package."""

    return resources.read_text("REMOLib.pygame_render", filename)


def _safe_set_uniform(shader: Shader, name: str, value) -> None:
    """Set a shader uniform if the target program defines it."""

    try:
        shader[name] = value
    except KeyError:
        # Silently ignore uniforms that are not present in the shader.
        pass


DynamicUniformCallback = Callable[["PostProcessEffect"], Dict[str, float | tuple]]


@dataclass
class PostProcessEffect:
    """Container describing a single full-screen post-processing pass."""

    name: str
    shader: Shader
    uniforms: Dict[str, float | tuple] = field(default_factory=dict)
    dynamic_uniforms: Optional[DynamicUniformCallback] = None

    def configure(self, **uniforms) -> "PostProcessEffect":
        """Update the static uniform values for the effect."""

        self.uniforms.update(uniforms)
        return self

    def set_dynamic_uniforms(self, callback: DynamicUniformCallback) -> "PostProcessEffect":
        """Register a callback that injects per-frame uniform values."""

        self.dynamic_uniforms = callback
        return self

    def prepare(self, source_tex: Texture, destination: Layer) -> None:
        """Populate uniforms prior to rendering the pass."""

        shader = self.shader
        _safe_set_uniform(shader, "imageTexture", source_tex)
        texel_size = (1.0 / source_tex.width, 1.0 / source_tex.height)
        _safe_set_uniform(shader, "texelSize", texel_size)
        resolution = (float(source_tex.width), float(source_tex.height))
        _safe_set_uniform(shader, "resolution", resolution)
        _safe_set_uniform(shader, "alpha", 1.0)

        if self.dynamic_uniforms:
            dynamic_values = self.dynamic_uniforms(self)
            for key, value in dynamic_values.items():
                _safe_set_uniform(shader, key, value)

        for key, value in self.uniforms.items():
            _safe_set_uniform(shader, key, value)


class PostProcessPipeline:
    """Manages a list of :class:`PostProcessEffect` objects."""

    def __init__(self, engine: RenderEngine, render_size: tuple[int, int]):
        self._engine = engine
        self._render_size = render_size
        self._effects: List[PostProcessEffect] = []
        self._buffers: List[Layer] = [
            self._engine.make_layer(render_size),
            self._engine.make_layer(render_size),
        ]

        self._vertex_src = _read_shader_source("vertex.glsl")
        self._builtin_factories = {
            "bloom": self._create_bloom_effect,
            "crt": self._create_crt_effect,
            "color_grade": self._create_color_grade_effect,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def effects(self) -> List[PostProcessEffect]:
        return self._effects

    def clear(self) -> None:
        self._effects.clear()

    def use(self, *effects: str | PostProcessEffect) -> None:
        """Replace the current chain with the provided effects."""

        self.clear()
        for effect in effects:
            if isinstance(effect, str):
                self._effects.append(self.create(effect))
            else:
                self._effects.append(effect)

    def create(self, name: str, **uniforms) -> PostProcessEffect:
        """Create one of the built-in post-process effects."""

        if name not in self._builtin_factories:
            raise ValueError(f"Unknown post-process effect: {name}")
        effect = self._builtin_factories[name]()
        if uniforms:
            effect.configure(**uniforms)
        return effect

    def bloom(self, **uniforms) -> PostProcessEffect:
        return self.create("bloom", **uniforms)

    def crt(self, **uniforms) -> PostProcessEffect:
        return self.create("crt", **uniforms)

    def color_grade(self, **uniforms) -> PostProcessEffect:
        return self.create("color_grade", **uniforms)

    def update(self, name: str, **uniforms) -> None:
        """Adjust uniforms for the first effect matching *name*."""

        for effect in self._effects:
            if effect.name == name:
                effect.configure(**uniforms)
                return
        raise ValueError(f"Effect '{name}' is not part of the current chain")

    def set_render_size(self, size: tuple[int, int]) -> None:
        """Resize the internal ping-pong buffers."""

        if size == self._render_size:
            return

        for buffer in self._buffers:
            buffer.release()

        self._render_size = size
        self._buffers = [
            self._engine.make_layer(size),
            self._engine.make_layer(size),
        ]

    def apply(self, source_texture: Texture) -> Texture:
        """Run the configured effects and return the final texture."""

        if not self._effects:
            return source_texture

        current_tex = source_texture
        toggle = 0
        for idx, effect in enumerate(self._effects):
            target_layer = self._buffers[toggle]
            effect.prepare(current_tex, target_layer)
            self._engine.render(current_tex, target_layer, shader=effect.shader)
            current_tex = target_layer.texture
            toggle = 1 - toggle

        return current_tex

    # ------------------------------------------------------------------
    # Built-in effects
    # ------------------------------------------------------------------
    def _make_shader(self, fragment_source: str) -> Shader:
        return self._engine.make_shader(self._vertex_src, fragment_source)

    def _create_bloom_effect(self) -> PostProcessEffect:
        shader = self._make_shader(_read_shader_source("postprocess_bloom.glsl"))
        effect = PostProcessEffect(
            name="bloom",
            shader=shader,
            uniforms={
                "bloomIntensity": 1.1,
                "bloomThreshold": 0.65,
                "bloomSoft": 0.35,
                "bloomRadius": 1.0,
            },
        )
        return effect

    def _create_crt_effect(self) -> PostProcessEffect:
        shader = self._make_shader(_read_shader_source("postprocess_crt.glsl"))

        def _dynamic(effect: PostProcessEffect) -> Dict[str, float]:
            return {"time": pygame.time.get_ticks() / 1000.0}

        effect = PostProcessEffect(
            name="crt",
            shader=shader,
            uniforms={
                "crtCurvature": 0.12,
                "crtScanlineIntensity": 0.25,
                "crtMaskStrength": 0.15,
                "crtVignette": 0.4,
            },
            dynamic_uniforms=_dynamic,
        )
        return effect

    def _create_color_grade_effect(self) -> PostProcessEffect:
        shader = self._make_shader(_read_shader_source("postprocess_color_grade.glsl"))
        effect = PostProcessEffect(
            name="color_grade",
            shader=shader,
            uniforms={
                "colorExposure": 1.0,
                "colorContrast": 1.05,
                "colorSaturation": 1.1,
                "colorOffset": (0.0, 0.0, 0.0),
                "colorGamma": 1.0,
            },
        )
        return effect

    # ------------------------------------------------------------------
    # Clean-up
    # ------------------------------------------------------------------
    def release(self) -> None:
        for buffer in self._buffers:
            buffer.release()
        self._buffers.clear()
        self._effects.clear()


__all__ = [
    "PostProcessEffect",
    "PostProcessPipeline",
]
