#version 330 core
in vec2 uv;
out vec4 color;

uniform vec4 brushcolor;
uniform float opacity;
uniform float diam;
uniform vec2 mpos;
uniform vec2 winsize;
uniform sampler2D basetexture;
uniform int showcolor;
uniform float softness;

#define line 2.0    // width of lines drawn * 2

void main() {
    vec3 texcolor = texture( basetexture, uv ).rgb;
    // vec3 brushcolor = vec3(br, bg, bb);
    
    float screenratio = winsize.y/winsize.x;
    float px = (1/winsize.y)*0.5;
    
    vec2  dpos = vec2(uv.x/screenratio, uv.y) - vec2(mpos.x/screenratio, mpos.y);
    float dist = sqrt(dot(dpos, dpos));
    float dr = diam*px;
    float lr = line*px;
    
    float cl = clamp((pow(dr - dist, softness))*2.0, 0, 1)*showcolor;
    
    // float wl = clamp((diam*winsize.y*0.5) + 0.5 - distance(uv*winsize.y,mpos*winsize.y), 0.0, 1.0);
    float wl = 1.0 - (1.0 + smoothstep( dr, dr+lr, dist)
                          - smoothstep( dr-lr, dr, dist));
    
    dr = (diam+line)*px;
    float bl = 1.0 - (1.0 + smoothstep( dr, dr+lr, dist)
                          - smoothstep( dr-lr, dr, dist));
    
    float opac = min(max(opacity, 0.2), 0.6);
    color.rgb = mix(texcolor, brushcolor.rgb, cl);
    color.rgb = mix(color.rgb, vec3(0.0), bl*opac);
    color.rgb = mix(color.rgb, vec3(1.0), wl*opac);
    color.a = 1.0;
}
