# encoding: utf-8
#!python3

from scene import *
from math import pi, cos, sin, atan
import asyncio
import websockets
import threading
import pickle
import struct
import time
from io import BytesIO

server_address = "ws://boiling-caverns-15454.herokuapp.com:80"

update_freq = 1.0/20.0

new_connection = bytes([0x0])
disconnect = bytes([0x5])

send_info = bytes([0x1])

get_all = bytes([0x2])
get_setup = bytes([0x3])
get_update = bytes([0x4])

def encode(obj):
	b = BytesIO()
	pickle.dump(obj, b)
	return b.getvalue()
	
def decode(obj):
	return pickle.loads(obj)
	
def encid(obj):
	return struct.pack('H', obj)
	
def decid(obj):
	return struct.unpack('H', obj)[0]

with open("sun.fsh") as f:
	sun_shader = f.read()

with open("dial.fsh") as f:
	dial_shader = Shader(f.read())

with open("power.fsh") as f:
	power_shader = Shader(f.read())

class ServerAccess (threading.Thread):
	def run(self):
		self.address = server_address
		self.loop = asyncio.new_event_loop()
		self.has_setup = False
		self.should_terminate = False
		self.tanks_data = {}
		
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(self.action())
	
	async def action(self):
		async with websockets.connect(self.address) as websocket:
			
			# make server connection & get id
			await websocket.send(new_connection)
			self.id_num = decid(await websocket.recv())
			
			# send/get data
			while True:
				d = dict(nickname = "xander", position = (game.tanks[0].position.x, game.tanks[0].position.y), arm_angle = game.tanks[0].arm_angle, color = game.tanks[0].color, model = "original")
				message = encid(self.id_num) + send_info + encode(d)
				await websocket.send(message)
				await websocket.send(encid(self.id_num) + get_all)
				tankdata = decode(await websocket.recv())
				del tankdata[self.id_num]
				for idnum, tank in tankdata.items():
					if idnum in self.tanks_data:
						for name, attr in tank.items():
								self.tanks_data[idnum][name] = attr
					else:
						self.tanks_data[idnum] = tank
				if self.should_terminate:
					await websocket.send(encid(self.id_num) + disconnect)
					break
				time.sleep(update_freq)
	def stop(self):
		self.should_terminate = True
	def update(self):
		if hasattr(game, "tanks"):
			if not self.has_setup:
				d = dict(nickname = "xander", position = (game.tanks[0].position.x, game.tanks[0].position.y), arm_angle = game.tanks[0].arm_angle, color = game.tanks[0].color, model = "original")
				message = encid(self.id_num) + send_info + encode(d)
				self.send(message)
				tankdata = decode(self.sendrecv(encid(self.id_num) + get_all))
			else:
				d = dict(position = game.tanks[0].position, arm_angle = game.tanks[0].arm_angle)
				message = encid(self.id_num) + send_info + encode(d)
				self.send(message)
				tankdata = decode(self.sendrecv(encid(self.id_num) + get_update))
			del tankdata[self.id_num]
			for idnum, tank in tankdata.items():
				if idnum in self.tanks_data:
					for name, attr in tank.items():
							self.tanks_data[idnum][name] = attr
				else:
					self.tanks_data[idnum] = tank
		if self.should_terminate:
			self.cleanup()
			return
		t = threading.Timer(update_freq, self.update)
		t.start()

	async def sendcoro(self, data):
		async with websockets.connect(self.address) as websocket:
			await websocket.send(data)
	async def recvcoro(self, future):
		async with websockets.connect(self.address) as websocket:
			data = await websocket.recv()
			future.set_result(data)
	async def sendrecvcoro(self, data, future):
		async with websockets.connect(self.address) as websocket:
			await websocket.send(data)
			data = await websocket.recv()
			future.set_result(data)
	def send(self, bytes):
		asyncio.set_event_loop(self.loop)
		self.loop.run_until_complete(self.sendcoro(bytes))
	def recv(self):
		asyncio.set_event_loop(self.loop)
		future = asyncio.Future()
		asyncio.ensure_future(self.recvcoro(future))
		self.loop.run_until_complete(future)
		return future.result()
	def sendrecv(self, bytes):
		asyncio.set_event_loop(self.loop)
		future = asyncio.Future()
		asyncio.ensure_future(self.sendrecvcoro(bytes, future))
		self.loop.run_until_complete(future)
		return future.result()
	
class Slider (object):
	def __init__(self, x, y, w, h):
		self.frame = Rect(x, y, w, h)
		self.position = .5
		self.abs_position = .5
		self.slider_size = Size(.7, .7) * self.frame.h*.8
		self.touch = None
	def draw(self):
		bg = Rect(self.frame.x, self.frame.y, self.frame.w, self.frame.h)
		start = self.frame.x + self.frame.w*.1
		width = self.frame.w*.8
		slider = Rect(start + width*self.position - self.slider_size.w/2.0, self.frame.y + self.frame.h/2.0 - self.slider_size.h/2.0, self.slider_size.w, self.slider_size.h)
		fill(.81)
		no_stroke()
		#rect(bg.x, bg.y, bg.w, bg.h)
		stroke_weight(2)
		stroke(0)
		line(start, self.frame.y + self.frame.h/2.0, start + width, self.frame.y + self.frame.h/2.0)
		no_stroke()
		fill(.35, .0, .81)
		use_shader(dial_shader)
		rect(slider.x, slider.y, slider.w, slider.h)
		use_shader()
	def touch_began(self, touch):
		start = self.frame.x + self.frame.w*.1
		width = self.frame.w*.8
		slider = Rect(start + width*self.position - self.slider_size.w/2.0, self.frame.y + self.frame.h/2.0 - self.slider_size.h/2.0, self.slider_size.w, self.slider_size.h)
		if touch.location in slider:
			self.touch = touch
	def touch_moved(self, touch):
		if self.touch != None and touch.touch_id == self.touch.touch_id:
			self.abs_position += (touch.location.x - touch.prev_location.x)/(self.frame.w*.8)
		self.position = min(max(self.abs_position, 0.0), 1.0)
	def touch_ended(self, touch):
		if self.touch != None and touch.touch_id == self.touch.touch_id:
			self.touch = None

class PowerSlider (Slider):
	def __init__(self, *args, **kwargs):
		Slider.__init__(self, *args, **kwargs)
	def draw(self):
		bg = Rect(self.frame.x, self.frame.y, self.frame.w, self.frame.h)
		start = self.frame.x + self.frame.w*.1
		width = self.frame.w*.8
		slider = Rect(start + width*self.position - self.slider_size.w/2.0, self.frame.y + self.frame.h/2.0 - self.slider_size.h/2.0, self.slider_size.w, self.slider_size.h)
		power_shader.set_uniform("slider", self.position)
		bg = bg.inset(10, 0)
		use_shader(power_shader)
		rect(bg.x, bg.y, bg.w, bg.h)
		use_shader()
		"""
		stroke_weight(2)
		stroke(0)
		line(start, self.frame.y + self.frame.h/2.0, start + width, self.frame.y + self.frame.h/2.0)
		no_stroke()
		fill(.35, .0, .81)
		use_shader(dial_shader)
		rect(slider.x, slider.y, slider.w, slider.h)
		use_shader()
		"""

class Tank (object):
	def __init__(self, position, color, name, parent):
		self.position = position
		self.name = name
		self.parent = parent
		self.size = Size(60, 60)
		self.angle = 0
		self.color = color
		self.arm_angle = 0
	def draw(self):
		x = (self.position.x/self.parent.bounds.w)
		self.position.y = self.parent.bounds.h*self.parent.terrain_func(x)
		# estimate the derivitave
		dx = .1
		# to the left
		dy_l = self.parent.terrain_func(x) - self.parent.terrain_func(x-dx)
		dydx_l = dy_l/dx
		# to the right
		dy_r = self.parent.terrain_func(x+dx) - self.parent.terrain_func(x)
		dydx_r = dy_r/dx
		#avg them
		dydx = (dydx_l + dydx_r)/2.0
		self.angle = atan(dydx)*(360/(2.0*pi))
		
		push_matrix()
		
		translate(self.position.x, self.position.y)
		rotate(self.angle)
		translate(-self.size.w/2.0, 0)
		scale(self.size.w/100.0, self.size.h/100.0)
		
		scaleout = (100.0/self.size.w)
		push_matrix()
		translate(scaleout*self.size.w/2.0, self.size.h)
		rotate(self.arm_angle)
		fill(.43, .43, .43)
		rect(-10, 0, 20, 70)
		
		
		pop_matrix()
		
		v = [(0, 30), (10, 30), (10, 70), (100, 30), (90, 70), (90, 30)]
		fill(self.color)
		triangle_strip(v)
		ellipse(20, 45, 60, 45)
		fill(0)
		ellipse(-15, 0, 30, 30)
		ellipse(85, 0, 30, 30)
		rect(0, 0, 100, 30)
		fill(.4)
		stroke(.9)
		stroke_weight(0)
		treadcirclesize = 23
		treads = 4.0
		for i in range(int(treads)+1):
			start = i/treads
			ellipse(start*100.0 - treadcirclesize/2.0, 15 - treadcirclesize/2.0, treadcirclesize, treadcirclesize)
		pop_matrix()

class Button (object):
	def __init__(self, x, y, w, h, onpress):
		self.onpress = onpress
		self.frame = Rect(x, y, w, h)
		self.tap = None
	def touch_began(self, touch):
		if self.tap == None:
			self.tap = touch
	def touch_moved(self, touch):
		if self.tap and touch.touch_id == self.tap.touch_id:
			self.tap = None
	def touch_ended(self, touch):
		if self.tap and self.tap.touch_id == touch.touch_id:
			if touch.location in self.frame:
				self.onpress()
			self.tap = None
						
class Tanks (Scene):
	def terrain_func(self, x):
			return (-cos(x*(pi*4.0)))/50.0 + 1/4.0
	def setup(self):
		self.tanks = [Tank(Point(self.bounds.w*.25, 0), (.06, .5, .77), "Blue", self)]
		self.turn = 0
		self.tap = None
		self.terraincolor = (.77, .27, .1)
		
		self.sunshader = Shader(sun_shader)
		
		self.angle_slider = Slider(self.bounds.w*.1, self.bounds.h*.9, self.bounds.w*.3, self.bounds.h*.1)
		self.power_slider = PowerSlider(self.bounds.w*.5, self.bounds.h*.9, self.bounds.w*.3, self.bounds.h*.1)
		self.sliders = [self.angle_slider, self.power_slider]
		
		self.moveleft = Rect(self.bounds.w*.8, self.bounds.h*.8, self.bounds.w*.1, self.bounds.h*.1)
		self.moveright = Rect()
		
		self.firebutton = Button(self.bounds.w*.45 - self.bounds.h*.05, self.bounds.h*.9, self.bounds.h*.1, self.bounds.h*.1, self.fire_button_pressed)
		self.firebutton.frame = self.firebutton.frame.inset(7, 7)
		
		self.buttons = [self.firebutton]
		
		self.finished = True
		
		access.start() # connects to server and stuff

	def draw(self):
		if not hasattr(self, "finished"):
			return
		#use_shader(self.defaultshader)
		background(.3, .66, .9)
		stroke_weight(0)
		density = 100
		fill(.91, .83, .53)
		for i in range(density):
			start = i/float(density)
			end = (i+1.)/float(density)
			smaller = min(self.terrain_func(start), self.terrain_func(end))
			
			bl = Vector2(start*self.bounds.w, 0)
			width = Vector2((end-start)*game.bounds.w, 0)
			height = Vector2(0, smaller*self.bounds.h)
			v = [bl, bl + width, bl + height, bl + width, bl + width + height, bl + height]
			triangle_strip(v)
			
			if self.terrain_func(start) < self.terrain_func(end):
				v = [(start*self.bounds.w, self.terrain_func(start)*self.bounds.h), (end*self.bounds.w, self.bounds.h*self.terrain_func(start)), (end*self.bounds.w, self.bounds.h*self.terrain_func(end))]
			else:
				v = [(start*self.bounds.w, self.terrain_func(end)*self.bounds.h), (end*self.bounds.w, self.bounds.h*self.terrain_func(end)), (start*self.bounds.w, self.bounds.h*self.terrain_func(start))]
			triangle_strip(v)
		
		
		# handle moving (~~shitty~~ it's okay though)
		tank = self.tanks[self.turn]
		for touch in self.touches.values():
			if self.angle_slider.touch != None and touch.touch_id == self.angle_slider.touch.touch_id:
				continue
			if touch.location.x > self.bounds.w/2.0:
				tank.position.x += 1
			else:
				tank.position.x -= 1
		tank.arm_angle = -self.angle_slider.position*180 + 90
		for tank in self.tanks:
			tank.draw()
		
		tanks = []
		#print("number of tanks: {}".format(len(access.tanks_data) + 1))
		#print("data: {!r}".format(access.tanks_data))
		if hasattr(access, "tanks_data"):
			for idnum, info in access.tanks_data.items():
				if "position" in info and "color" in info and "nickname" in info and "arm_angle" in info:
					t = Tank(info["position"], info["color"], info["nickname"], self)
					t.arm_angle = info["arm_angle"]
					t.position = Point(t.position[0], t.position[1])
					tanks.append(t)
		for t in tanks:
			t.draw()
		
		# sun
		use_shader(self.sunshader)
		rect(self.bounds.w*.03, self.bounds.h*.6, self.bounds.h*.25, self.bounds.h*.25)
		use_shader()
		
		# draw ui
		fill(.8, .8, .8)
		rect(0, self.bounds.h*.9, self.bounds.w, self.bounds.h*.1)
		# angle slider
		self.angle_slider.draw()
		a = str(int(self.angle_slider.position*180 - 90))
		self.power_slider.draw()
		tint(0,0,0)
		text(a + "˚", x = self.bounds.w*.05, y = self.bounds.h*.95, font_size = 40)
		
		# fire button
		fill(1,0,0)
		stroke(0,0,0)
		stroke_weight(2)
		fireframe = self.firebutton.frame
		ellipse(fireframe.x, fireframe.y, fireframe.w, fireframe.h)
		text("fire", x = fireframe.center().x, y = fireframe.center().y)
	def fire_button_pressed(self):
		self.next_turn()
		# fire the cannon...

	def next_turn(self):
		self.turn = (self.turn + 1) % len(self.tanks)
		self.angle_slider.position = 1.0 - (self.tanks[self.turn].arm_angle + 90)/180.0
		self.angle_slider.abs_position = self.angle_slider.position
		
	def touch_began(self, touch):
		for slider in self.sliders:
			slider.touch_began(touch)
		for button in self.buttons:
			button.touch_began(touch)
	def touch_moved(self, touch):
		for slider in self.sliders:
			slider.touch_moved(touch)
		for button in self.buttons:
			button.touch_began(touch)
	def touch_ended(self, touch):
		for slider in self.sliders:
			slider.touch_ended(touch)
		for button in self.buttons:
			button.touch_ended(touch)
	def stop(self):
		access.stop()

game = Tanks()
access = ServerAccess()
access.daemon = True
run(game, show_fps = True)
