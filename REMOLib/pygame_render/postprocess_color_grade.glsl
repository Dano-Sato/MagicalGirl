#version 330 core

in vec2 fragmentTexCoord;

uniform sampler2D imageTexture;
uniform float alpha;

uniform float colorExposure;
uniform float colorContrast;
uniform float colorSaturation;
uniform vec3 colorOffset;
uniform float colorGamma;

out vec4 color;

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

void main() {
    vec3 base = texture(imageTexture, fragmentTexCoord).rgb;

    vec3 exposure = base * colorExposure;

    vec3 contrasted = (exposure - 0.5) * colorContrast + 0.5;

    float luma = luminance(contrasted);
    vec3 grey = vec3(luma);
    vec3 saturated = mix(grey, contrasted, colorSaturation);

    vec3 offset = saturated + colorOffset;
    vec3 graded = pow(max(offset, vec3(0.0)), vec3(1.0 / max(colorGamma, 1e-4)));

    color = vec4(graded, alpha);
}
