#version 330
in vec2 uv;
out vec4 color;

uniform sampler2D basetex;

void main() {
    color = texture( basetex, uv ).rgba;
    // color.a = 1.0;
}
