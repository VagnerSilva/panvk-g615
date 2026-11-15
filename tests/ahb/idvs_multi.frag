#version 450
layout(location = 0) in vec2 smooth_color;
layout(location = 1) flat in vec2 flat_color;
layout(location = 0) out vec4 output_color;
void main()
{
    output_color = vec4(smooth_color, flat_color.x * 0.25, 1.0);
}
