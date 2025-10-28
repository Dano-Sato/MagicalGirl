#version 330 core

in vec2 fragmentTexCoord;      // 텍스처 좌표
uniform sampler2D imageTexture; // 이미지 텍스처
uniform vec2 texelSize;         // 텍셀 크기 (1.0 / 화면 해상도)
uniform float alpha;            // 투명도 조절

out vec4 color;

void main()
{
    // 현재 픽셀과 이웃 픽셀의 색상 샘플링
    vec4 colorCenter = texture(imageTexture, fragmentTexCoord);
    vec4 colorLeft   = texture(imageTexture, fragmentTexCoord - vec2(texelSize.x, 0.0));
    vec4 colorRight  = texture(imageTexture, fragmentTexCoord + vec2(texelSize.x, 0.0));
    vec4 colorTop    = texture(imageTexture, fragmentTexCoord + vec2(0.0, texelSize.y));
    vec4 colorBottom = texture(imageTexture, fragmentTexCoord - vec2(0.0, texelSize.y));
    vec4 colorTopLeft = texture(imageTexture, fragmentTexCoord + vec2(-texelSize.x, texelSize.y));
    vec4 colorTopRight = texture(imageTexture, fragmentTexCoord + vec2(texelSize.x, texelSize.y));
    vec4 colorBottomLeft = texture(imageTexture, fragmentTexCoord + vec2(-texelSize.x, -texelSize.y));
    vec4 colorBottomRight = texture(imageTexture, fragmentTexCoord + vec2(texelSize.x, -texelSize.y));

    // 주위 픽셀 간의 색상 차이 계산 (경계 강도 측정)
    float edgeStrength = length(colorCenter.rgb - colorRight.rgb) 
                       + length(colorCenter.rgb - colorLeft.rgb)
                       + length(colorCenter.rgb - colorTop.rgb)
                       + length(colorCenter.rgb - colorBottom.rgb)
                       + 0.5 * (length(colorCenter.rgb - colorTopLeft.rgb) 
                       + length(colorCenter.rgb - colorTopRight.rgb)
                       + length(colorCenter.rgb - colorBottomLeft.rgb)
                       + length(colorCenter.rgb - colorBottomRight.rgb));

    // 경계 감지 민감도와 블렌딩 비율 조정
    float blendWeight = clamp(edgeStrength * 4.0, 0.0, 1.0);

    // 블렌딩된 색상 계산 (주위 픽셀의 가중 평균 색상 적용)
    vec3 blendedColor = mix(colorCenter.rgb, 
                            (colorLeft.rgb + colorRight.rgb + colorTop.rgb + colorBottom.rgb 
                             + 0.5 * (colorTopLeft.rgb + colorTopRight.rgb + colorBottomLeft.rgb + colorBottomRight.rgb)) / 6.0, 
                            blendWeight);

    // 최종 색상에 알파 값 적용
    color = vec4(blendedColor, colorCenter.a * alpha);
}
