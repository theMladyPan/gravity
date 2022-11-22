#version 330

in vec4 in_vertex; // XYZW
in vec4 in_color; // RGBA

out vec2 vertex_pos; // XY
out float vertex_radius; // W
out vec4 vertex_color;

void main()
{
    vertex_pos = in_vertex.xy;
    vertex_radius = in_vertex.w;
    vertex_color = in_color;
}