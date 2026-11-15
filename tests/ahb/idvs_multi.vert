#version 450
layout(location = 0) in vec2 pos;
layout(location = 0) out vec2 smooth_color;
layout(location = 1) flat out vec2 flat_color;
layout(push_constant) uniform Params {
    float x_offset;
    float red_scale;
} pc;
void main()
{
    gl_Position = vec4(pos.x + pc.x_offset, pos.y, 0.0, 1.0);
    smooth_color = vec2((pos.x + 1.0) * pc.red_scale, pos.y + 1.0);
    flat_color = pos + 2.0;
}
