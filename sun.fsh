precision highp float;
varying vec2 v_tex_coord;
// These uniforms are set automatically:
uniform sampler2D u_texture;
uniform float u_time;
uniform vec2 u_sprite_size;

# define edge .02
# define pi 3.1415926535

float triangle(vec2 pt1, vec2 pt2, vec2 pt3, vec2 c) {
	vec2 v0 = pt2 - pt1;
	vec2 v1 = pt3 - pt1;
	vec2 v2 = c - pt1;
	float dot00 = dot(v0, v0);
	float dot01 = dot(v0, v1);
	float dot02 = dot(v0, v2);
	float dot11 = dot(v1, v1);
	float dot12 = dot(v1, v2);
	float invDenom = 1.0/(dot00 * dot11 - dot01 * dot01);
	float u = (dot11 * dot02 - dot01 * dot12) * invDenom;
	float v = (dot00 * dot12 - dot01 * dot02) * invDenom;
	
	float val = 100.0;	

	val = min(smoothstep(-edge, edge, u), val);
	val = min(smoothstep(-edge, edge, v), val);
	val = min(smoothstep(1.0 + edge, 1.0 - edge, v+u), val);

	return val;
}

void main(void) {
	vec2 uv = v_tex_coord;
   	vec4 bg = vec4(0.0);
	vec4 col = vec4(1.0, 1.0, 0.0, 1.0);
	
	float radius = .25;
	float centerDist = length(uv - .5);
	float val = smoothstep(radius + edge/7.0, radius - edge/7.0, centerDist);
	
	int flames = 10;
	float full = 2.0*pi;
	float width = .5;
	float height = .1;
	float hoverc = .03;

	float t = u_time/7.0;	

	for (int i = 0; i < flames; i++) {
		float hover = hoverc + sin(float(i)*10. - t*20.0)*.005;

		float a1 = t + full*(float(i) - width/2.0)/float(flames);
		float a2 = t + full*(float(i))/float(flames);
		float a3 = t + full*(float(i) + width/2.0)/float(flames);
		vec2 p1 = .5 + vec2(cos(a1), sin(a1))*(radius + hover);
		vec2 p2 = .5 + vec2(cos(a2), sin(a2))*(radius + hover + height);
		vec2 p3 = .5 + vec2(cos(a3), sin(a3))*(radius + hover);
		val += triangle(p1, p2, p3, uv);
	}
	
	gl_FragColor = mix(bg, col, val);
}
