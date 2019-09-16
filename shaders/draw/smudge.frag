#version 330 core
in vec2 uv;
out vec4 color;

uniform float radius;
uniform float pressure;
uniform vec2 mpos;
uniform vec2 motion;
uniform float sz;
uniform float px;

uniform sampler2D basetexture;

#define PI 3.1415926535897932384626433832795
// #define sz 512.0
// #define px 1.0/sz

void main() {
    vec4 texcolor = texture( basetexture, uv );
    vec4 precolor = texture( basetexture, vec2(uv.x + (px*motion.x), uv.y + (px*motion.y)));
    vec2 uv_px = uv * sz;
    
    float cd = clamp(radius + 0.5 - distance(uv_px, mpos), 0.0, 1.0);
    float soft = 0.5 - cos( clamp( 1.0 - sqrt( distance(uv_px, mpos) / radius ), 0.0, 1.0 ) * PI) * 0.5;
    float str = clamp( mix( cd, soft, 1.0-pressure ) * pressure, 0.0, 1.0 );
    color = mix(texcolor, precolor, str);
}
