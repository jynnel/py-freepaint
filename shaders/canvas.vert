#version 330 core
in vec3 vertexpos;
in vec2 vertexuv;
out vec2 uv;

uniform mat4 transform;

void main() {
    gl_Position = transform * vec4( vertexpos, 1.0 );
    uv = vertexuv;
}
