#version 330 core
in vec2 uv;
out vec4 color;

uniform sampler2D basetexture;

void main() {
    color = texture( basetexture, uv ).rgba;
    // color += vec4( uv.x*0.2, uv.y*0.2, 0.4*0.2, 1.0 );
}
