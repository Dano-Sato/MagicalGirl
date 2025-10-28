#version 330 core

in vec2 fragmentTexCoord; // top-left is [0, 1] and bottom-right is [1, 0]
uniform sampler2D imageTexture; // texture in location 0
uniform float alpha;            // transparency level, where 1.0 is fully opaque

out vec4 color;

void main()
{
    // 텍스처의 색상을 가져오고, 알파 값을 곱하여 투명도 조절
    vec4 texColor = texture(imageTexture, fragmentTexCoord);
    color = vec4(texColor.rgb, texColor.a * alpha);
}