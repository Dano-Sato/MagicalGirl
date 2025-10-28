#version 330 core

in vec2 fragmentTexCoord;

uniform sampler2D imageTexture;
uniform vec2 texelSize;
uniform vec2 resolution;
uniform float alpha;

uniform float crtCurvature;
uniform float crtScanlineIntensity;
uniform float crtMaskStrength;
uniform float crtVignette;
uniform float time;

out vec4 color;

vec2 barrel_distortion(vec2 coord, float strength) {
    vec2 cc = coord * 2.0 - 1.0;
    float dist = dot(cc, cc);
    cc *= 1.0 + strength * dist;
    return cc * 0.5 + 0.5;
}

void main() {
    vec2 uv = barrel_distortion(fragmentTexCoord, crtCurvature);

    if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
        color = vec4(0.0, 0.0, 0.0, alpha);
        return;
    }

    vec3 base = texture(imageTexture, uv).rgb;

    // Scanlines
    float scanline = sin((uv.y * resolution.y) * 3.14159);
    float scanline_mask = 1.0 - crtScanlineIntensity * (0.5 * (scanline + 1.0));

    // Shadow mask
    vec2 mask_uv = uv * resolution.xy;
    float mask = sin(mask_uv.x * 3.14159) * sin(mask_uv.y * 3.14159);
    float shadow_mask = 1.0 - crtMaskStrength * (mask * 0.5 + 0.5);

    // Subtle flicker
    float flicker = 1.0 + 0.01 * sin(time * 120.0);

    // Vignette
    vec2 centered = uv - 0.5;
    float vignette = 1.0 - crtVignette * dot(centered, centered) * 2.2;
    vignette = clamp(vignette, 0.0, 1.0);

    vec3 result = base * scanline_mask * shadow_mask * vignette * flicker;
    color = vec4(result, alpha);
}
