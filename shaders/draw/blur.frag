#version 330 core
in vec2 uv;
out vec4 color;

uniform float opacity;
uniform float radius;
uniform vec2 mpos;

uniform sampler2D basetex;

#define sz 512.0
#define px 1.0/sz

vec4 blurcolor() {
    float pd = px*(radius / ((1.0-opacity) * radius * (1.0-(radius/220.f))));
    vec4 blurc = vec4(0.0);
    // top row
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y-(3.0*pd) ) ) * .00000067;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y-(3.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y-(3.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x         , uv.y-(3.0*pd) ) ) * .00038771;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y-(3.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y-(3.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y-(3.0*pd) ) ) * .00000067;
    // bot row
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y+(3.0*pd) ) ) * .00000067;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y+(3.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y+(3.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x         , uv.y+(3.0*pd) ) ) * .00038771;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y+(3.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y+(3.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y+(3.0*pd) ) ) * .00000067;
    // 2nd row down
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y-(2.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y-(2.0*pd) ) ) * .00078634;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y-(2.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x         , uv.y-(2.0*pd) ) ) * .01330373;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y-(2.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y-(2.0*pd) ) ) * .00078634;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y-(2.0*pd) ) ) * .00002292;
    // 2nd row up
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y+(2.0*pd) ) ) * .00002292;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y+(2.0*pd) ) ) * .00078634;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y+(2.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x         , uv.y+(2.0*pd) ) ) * .01330373;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y+(2.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y+(2.0*pd) ) ) * .00078634;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y+(2.0*pd) ) ) * .00002292;
    // 3rd row down
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y-(1.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y-(1.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y-(1.0*pd) ) ) * .05472157;
    blurc += texture( basetex, vec2(uv.x         , uv.y-(1.0*pd) ) ) * .11098164;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y-(1.0*pd) ) ) * .05472157;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y-(1.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y-(1.0*pd) ) ) * .00019117;
    // 3rd row up
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y+(1.0*pd) ) ) * .00019117;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y+(1.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y+(1.0*pd) ) ) * .05472157;
    blurc += texture( basetex, vec2(uv.x         , uv.y+(1.0*pd) ) ) * .11098164;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y+(1.0*pd) ) ) * .05472157;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y+(1.0*pd) ) ) * .00655965;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y+(1.0*pd) ) ) * .00019117;
    // center row
    blurc += texture( basetex, vec2(uv.x-(3.0*pd), uv.y          ) ) * .00038771;
    blurc += texture( basetex, vec2(uv.x-(2.0*pd), uv.y          ) ) * .01330373;
    blurc += texture( basetex, vec2(uv.x-(1.0*pd), uv.y          ) ) * .11098164;
    blurc += texture( basetex, vec2(uv.x         , uv.y          ) ) * .22508352;
    blurc += texture( basetex, vec2(uv.x+(1.0*pd), uv.y          ) ) * .11098164;
    blurc += texture( basetex, vec2(uv.x+(2.0*pd), uv.y          ) ) * .01330373;
    blurc += texture( basetex, vec2(uv.x+(3.0*pd), uv.y          ) ) * .00038771;
        
    return blurc;
}

void main() {
    vec4 texcolor  = texture( basetex, uv );
    vec2 uv_px = uv * sz;
    
    float cd = clamp(radius + 0.5 - distance(uv_px, mpos), 0.0, 1.0);
    color = mix(texcolor, blurcolor(), clamp(cd*opacity, 0.0, 1.0));
}
