#version 330 core
in vec3 v_pos;
in vec2 v_uv;
out vec2 uv;

// uniform mat4 trans;

void main() {
    gl_Position = vec4( v_pos, 1.0 );
    uv = v_uv;
}
