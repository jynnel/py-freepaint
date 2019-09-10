#version 330 core
in vec3 vertexpos;
in vec2 vertexuv;
out vec2 uv;

void main() {
    gl_Position = vec4( vertexpos, 1.0 );
    uv = vertexuv;
}
