#version 330
in vec2 uv;
out vec4 color;

uniform sampler1D basetex;

void main() {
    color = texture( basetex, 0 ).rgba;
    // color.a = 1.0;
}
