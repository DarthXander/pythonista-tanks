precision highp float;
varying vec2 v_tex_coord;
// These uniforms are set automatically:
uniform sampler2D u_texture;
uniform float u_time;
uniform vec2 u_sprite_size;

float sphere(vec2 c) {
	// c.x**2 + c.y**2 + z**2 = 1.
	// sqrt(1. - (c.x**2 + c.y**2)) = z
	c = c - .5;
	c *= 2.;
	float dist2 = pow(c.x, 2.0) + pow(c.y, 2.0);
	if (dist2 > 1.0) {
		return 0.;
	}
	return sqrt(1. - dist2);
}

vec3 spherenorm(vec2 c) {
	vec2 cn = c - .5; 
	cn *= 2.;
	vec3 norm = vec3(cn.x, cn.y, sphere(c));
	return norm;
}

void main(void) {
	vec2 uv = v_tex_coord;

	vec3 lightDir = vec3(-.5, .4, 1.0);
	lightDir = lightDir/length(lightDir);

	vec4 background = vec4(0.);
	vec4 ambient = vec4(.4, .4, .4, 1.0);
	vec4 reflect = vec4(.7, .7, .7, 1.0);
	vec4 specular = vec4(1.0, 1.0, 1.0, 1.0);

	float mixLevel = dot(lightDir, spherenorm(uv));
	float height = sphere(uv);
	gl_FragColor = mix(ambient, mix(reflect, specular, pow(mixLevel, 20.0)), mixLevel);
	//gl_FragColor = mix(ambient, reflect, mixLevel);
	
	float bg = smoothstep(.0, .3, height);
	gl_FragColor = mix(background, gl_FragColor, bg);
}
