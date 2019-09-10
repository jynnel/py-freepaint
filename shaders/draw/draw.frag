#version 330 core

in vec2 uv;
out vec4 color;

uniform vec4 incolor;
uniform vec4 mxcolor;
// uniform float mxpower;
uniform float soft;
uniform float radius;
uniform float press;
uniform float opacity;
uniform vec2 mpos;

uniform sampler2D basetex;

#define PI 3.1415926535897932384626433832795
#define sz 512.0
const float px = 1.0/sz;

float hardCircle(vec2 point, float radius) {
  float dist = distance(point, gl_FragCoord.xy);
  float circ = radius + 0.5 - dist;
  return clamp( circ, 0., 1. );
}

// p = pixel point, r = inner radius, outer radius
float smoothCircle(vec2 point, float radius, float soft) {
  float dist = distance(point, gl_FragCoord.xy);
  float circ = 1.0 - smoothstep(radius*soft - 0.5, radius + 0.5, dist);
  return clamp( circ, 0., 1.);
}

void main() {
  vec4 canv = texture2D( basetex, uv);
  
  float circ = 0.0;
  if( soft == -1.0 ) {
    circ = hardCircle(mpos, radius);
  } else {
    circ = ( smoothCircle(mpos, radius, soft ) );
  }
  
  float amt = clamp( circ * opacity, 0., 1. );
  
  color = vec4( mix( canv, incolor, amt ).rgb, 1.0 );
}
