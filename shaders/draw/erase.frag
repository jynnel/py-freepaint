#version 330 core
in vec2 uv;
out vec4 color;

uniform float softness;
uniform float radius;
uniform float opacity;
uniform vec2 mpos;
// uniform float px;

uniform sampler2D basetexture;

// #define PI 3.1415926535897932384626433832795
// #define sz 512.0
// #define px 1.0/sz

void main() {
    vec4 texcolor = texture( basetexture, uv );
    // float mask;
    
    // if( radius < 2.0 ) {
    //     // this adds some antialiasing (0.5 pixels) to the brush mask, while still using softness to affect opacity
    //     mask = clamp( (radius + 0.5 - distance(uv*sz, mpos)) * clamp(1.05 - softness, 0.0, 1.0), 0.0, 1.0);
    // }
    // else {
    //     // factoring in the softness amount at higher brush sizes; has major aliasing with a hard edge at low sizes
    //     // this is the formula I want to use, but the aliasing at low sizes is very bad
    //     mask = clamp( pow(1.0 - distance(uv*sz, mpos)/radius, softness), 0.0, 1.0 );
    // }
    
    
    // float opac = clamp( mask * opacity, 0.0, 1.0 );
    color = vec4(texcolor.rgb, 0.0);
}
