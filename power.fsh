precision highp float;
varying vec2 v_tex_coord;
// These uniforms are set automatically:
uniform sampler2D u_texture;
uniform float u_time;
uniform vec2 u_sprite_size;
uniform float slider;

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main(void) {
	vec2 uv = v_tex_coord;
	uv = (uv - .5)/.8 + .5;
	float shaded = slider;

	vec4 bg = vec4(0.);
	vec4 col1 = vec4(0.04, 1., 1.0, 1.0);
	vec4 col2 = vec4(0.29, 1., 1.0, 1.0);
	vec4 col = mix(col1, col2, 1.0-uv.x);
	vec4 barColor = vec4(0.0, 0.0, 0.0, 1.0);

	float edge = .01;
	float bottom = .5 - uv.x/2.0;
	float top = .5 + uv.x/2.0;
	float val = smoothstep(bottom - edge/2.0, bottom + edge/2.0, uv.y) - smoothstep(top - edge/2., top + edge/2.0, uv.y);
	val *= (smoothstep(shaded + edge/2.0, shaded - edge/2.0, uv.x) + .5)/1.5;
	val *= smoothstep(1.0 + edge/2.0, 1.0 - edge/2.0, uv.x);
	gl_FragColor = mix(bg, vec4(hsv2rgb(col.rgb), 1.0), val);
	
	float thickness = .01;
	float start = shaded - thickness/2.0;
	float end = shaded + thickness/2.0;
	float bar = smoothstep(start - edge/2.0, start + edge/2.0, uv.x) - smoothstep(end - edge/2., end + edge/2.0, uv.x);
	gl_FragColor = mix(gl_FragColor, barColor, bar);
}
