from __future__ import annotations

import math
from typing import Callable, Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .core import graphicObj

TAU = getattr(math, "tau", math.pi * 2)


def _to_vector(point: object) -> pygame.Vector2:
    """Convert *point* to :class:`pygame.Vector2` without importing core symbols."""

    if hasattr(point, "toTuple"):
        point = point.toTuple()  # type: ignore[assignment]
    if isinstance(point, (tuple, list)) and len(point) >= 2:
        return pygame.Vector2(float(point[0]), float(point[1]))
    raise TypeError("Anchor provider must return a tuple-like object with x/y coordinates.")


class GraphicEffect:
    """Base class for runtime driven :class:`graphicObj` effects."""

    def __init__(self, target: "graphicObj") -> None:
        self.target = target
        self._active = True
        self._enabled = True
        self._start_time = pygame.time.get_ticks()
        self._paused_at: Optional[int] = None

    @property
    def active(self) -> bool:
        return self._active

    @property
    def enabled(self) -> bool:
        return self._enabled

    def deactivate(self) -> None:
        self._active = False
        self._enabled = False

    def pause(self) -> None:
        if not self._enabled:
            return
        self._enabled = False
        self._paused_at = pygame.time.get_ticks()

    def resume(self) -> None:
        if self._enabled:
            return
        now = pygame.time.get_ticks()
        if self._paused_at is not None:
            self._start_time += now - self._paused_at
        self._paused_at = None
        self._enabled = True

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self.resume()
        else:
            self.pause()

    def reset(self) -> None:
        self._start_time = pygame.time.get_ticks()
        self._paused_at = None

    def reset_anchor(self) -> None:
        self.reset()

    def update(self, time_ms: int) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class GraphicEffectSystem:
    """Tracks active :class:`GraphicEffect` instances and updates them every frame."""

    _effects: list[GraphicEffect] = []

    @classmethod
    def add(cls, effect: GraphicEffect) -> GraphicEffect:
        cls._effects.append(effect)
        return effect

    @classmethod
    def remove(cls, effect: GraphicEffect) -> None:
        if effect in cls._effects:
            cls._effects.remove(effect)

    @classmethod
    def clear_for(cls, target: "graphicObj") -> None:
        cls._effects = [effect for effect in cls._effects if effect.target is not target]

    @classmethod
    def update(cls, time_ms: Optional[int] = None) -> None:
        if time_ms is None:
            time_ms = pygame.time.get_ticks()
        for effect in list(cls._effects):
            if not effect.active:
                cls._effects.remove(effect)
                continue
            if not effect.enabled:
                continue
            try:
                effect.update(time_ms)
            except Exception:
                cls._effects.remove(effect)
                raise


class FloatingEffect(GraphicEffect):
    """Makes a graphic object float up and down around an anchor point."""

    def __init__(
        self,
        target: "graphicObj",
        *,
        amplitude: float = 25,
        period: int = 2400,
        phase: float = 0.0,
    ) -> None:
        super().__init__(target)
        self.amplitude = amplitude
        self.period = max(period, 1)
        self.phase = phase
        self._anchor = _to_vector(target.center)

    def reset_anchor(self) -> None:
        super().reset_anchor()
        self._anchor = _to_vector(self.target.center)

    def update(self, time_ms: int) -> None:
        elapsed = (time_ms - self._start_time) / self.period
        offset = math.sin(self.phase + elapsed * TAU) * self.amplitude
        center = pygame.Vector2(self._anchor.x, self._anchor.y + offset)
        self.target.center = (int(round(center.x)), int(round(center.y)))


class SwayEffect(GraphicEffect):
    """Applies a subtle horizontal sway and rotation."""

    def __init__(
        self,
        target: "graphicObj",
        *,
        amplitude: float = 35,
        max_angle: float = 6,
        period: int = 2000,
        phase: float = 0.0,
    ) -> None:
        super().__init__(target)
        self.amplitude = amplitude
        self.max_angle = max_angle
        self.period = max(period, 1)
        self.phase = phase
        self._anchor = _to_vector(target.center)
        self._base_angle = getattr(target, "angle", 0)

    def reset_anchor(self) -> None:
        super().reset_anchor()
        self._anchor = _to_vector(self.target.center)
        self._base_angle = getattr(self.target, "angle", 0)

    def update(self, time_ms: int) -> None:
        elapsed = (time_ms - self._start_time) / self.period
        wave = math.sin(self.phase + elapsed * TAU)
        center = pygame.Vector2(self._anchor.x + wave * self.amplitude, self._anchor.y)
        self.target.center = (int(round(center.x)), int(round(center.y)))
        if hasattr(self.target, "angle"):
            self.target.angle = self._base_angle + wave * self.max_angle


class PulseAlphaEffect(GraphicEffect):
    """Animates the alpha value to create a breathing glow."""

    def __init__(
        self,
        target: "graphicObj",
        *,
        min_alpha: int = 120,
        max_alpha: int = 255,
        period: int = 1600,
        phase: float = 0.0,
    ) -> None:
        super().__init__(target)
        self.min_alpha = max(0, min(255, min_alpha))
        self.max_alpha = max(0, min(255, max_alpha))
        self.period = max(period, 1)
        self.phase = phase

    def update(self, time_ms: int) -> None:
        elapsed = (time_ms - self._start_time) / self.period
        wave = (math.sin(self.phase + elapsed * TAU) + 1) * 0.5
        alpha = int(round(self.min_alpha + (self.max_alpha - self.min_alpha) * wave))
        self.target.alpha = max(0, min(255, alpha))


class OrbitPulseEffect(GraphicEffect):
    """Rotate an object around an anchor while gently pulsing the orbit radius."""

    def __init__(
        self,
        target: "graphicObj",
        *,
        radius: float = 80.0,
        angular_speed: float = 90.0,
        radial_amplitude: float = 12.0,
        radial_period: int = 1800,
        clockwise: bool = False,
        phase: float = 0.0,
        rotate_with_motion: bool = False,
        anchor_getter: Optional[Callable[[], object]] = None,
    ) -> None:
        super().__init__(target)
        self.radius = radius
        self.angular_speed = angular_speed
        self.radial_amplitude = radial_amplitude
        self.radial_period = max(radial_period, 1)
        self.clockwise = clockwise
        self.phase = phase
        self.rotate_with_motion = rotate_with_motion and hasattr(target, "angle")
        self._anchor_getter = anchor_getter
        self._anchor = self._resolve_anchor()
        self._base_angle = getattr(target, "angle", 0)

    def _resolve_anchor(self) -> pygame.Vector2:
        if self._anchor_getter is not None:
            return _to_vector(self._anchor_getter())
        return _to_vector(self.target.center)

    def reset_anchor(self) -> None:
        super().reset_anchor()
        self._anchor = self._resolve_anchor()
        self._base_angle = getattr(self.target, "angle", 0)

    def update(self, time_ms: int) -> None:
        if self._anchor_getter is not None:
            self._anchor = self._resolve_anchor()
        elapsed = (time_ms - self._start_time) / 1000.0
        angle_radians = math.radians(self.angular_speed) * elapsed
        if self.clockwise:
            angle_radians *= -1
        if self.radial_amplitude != 0:
            radial_wave = math.sin(self.phase + elapsed * TAU / (self.radial_period / 1000.0))
        else:
            radial_wave = 0.0
        dynamic_radius = self.radius + radial_wave * self.radial_amplitude
        offset = pygame.Vector2(math.cos(angle_radians), math.sin(angle_radians)) * dynamic_radius
        center = self._anchor + offset
        self.target.center = (int(round(center.x)), int(round(center.y)))
        if self.rotate_with_motion:
            self.target.angle = self._base_angle + math.degrees(angle_radians)


__all__ = [
    "GraphicEffect",
    "GraphicEffectSystem",
    "FloatingEffect",
    "SwayEffect",
    "PulseAlphaEffect",
    "OrbitPulseEffect",
]
