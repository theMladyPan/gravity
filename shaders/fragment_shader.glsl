#version 330

in vec2 g_uv;
in vec3 g_color;
in float g_radius;
in vec2 g_origin;

out vec4 out_color;

uniform vec2 u_resolution;

void main()
{
    /*
    float l = length(vec2(0.5, .5) - g_uv.xy);
    if ( l > 1)
    {
        discard;
    }
    float alpha;
    if (l == 0.0)
        alpha = 1;
    else {
        alpha = min(1.0, 1 - l*2);
    }
    vec3 c = g_color.rgb;
    // c.xy += v_uv.xy * 0.05;
    // c.xy += v_pos.xy * 0.75;
    out_color = vec4(c, alpha);
    */

    float l = length(g_uv.xy - vec2(0.5, .5));
    float alpha = 1 - pow(l*3, 3);
    out_color = vec4(g_color.rgb, alpha);
}
