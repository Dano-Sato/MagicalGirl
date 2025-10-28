#version 330 core

in vec2 fragmentTexCoord;

uniform sampler2D imageTexture;
uniform vec2 texelSize;
uniform float alpha;

uniform float bloomIntensity;
uniform float bloomThreshold;
uniform float bloomSoft;
uniform float bloomRadius;

out vec4 color;

float luminance(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

void main() {
    vec3 base = texture(imageTexture, fragmentTexCoord).rgb;
    float brightness = luminance(base);

    float knee = bloomThreshold * bloomSoft + 1e-4;
    float softness = clamp((brightness - bloomThreshold + knee) / (2.0 * knee), 0.0, 1.0);
    float bloomAmount = max(brightness - bloomThreshold, 0.0) * softness;

    vec2 offsets[8] = vec2[](
        vec2(1.0, 0.0),
        vec2(-1.0, 0.0),
        vec2(0.0, 1.0),
        vec2(0.0, -1.0),
        vec2(1.0, 1.0),
        vec2(-1.0, 1.0),
        vec2(1.0, -1.0),
        vec2(-1.0, -1.0)
    );

    vec3 bloom = base;
    for (int i = 0; i < 8; ++i) {
        vec2 sampleOffset = offsets[i] * texelSize * bloomRadius;
        bloom += texture(imageTexture, fragmentTexCoord + sampleOffset).rgb;
    }

    bloom /= 9.0;
    vec3 result = base + bloom * bloomAmount * bloomIntensity;

    color = vec4(result, alpha);
}
