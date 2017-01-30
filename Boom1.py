import sys
import time
import csv
import pygame
import random
import RPi.GPIO as GPIO
import struct

GPIO.setmode(GPIO.BOARD)
PINS_IN = {
	'pir1': 8,
	'pir2': 10,	
	'pir3': 11,
	#'pir4': 11,
	'nacht': 13,
	'soundSensor': 15
}
PINS_OUT = {
	'rgb1': 3,
	'rgb2': 5,
	'rgb3': 7
}
PIR_PINS = []

def init_led_pins():
	Freq = 100 #Hz
	r = GPIO.PWM(PINS_OUT['rgb1'], Freq)
	r.start(0)
	g = GPIO.PWM(PINS_OUT['rgb2'], Freq)
	g.start(0)
	b = GPIO.PWM(PINS_OUT['rgb3'], Freq)
	b.start(0)
	return r, g, b
	 
def playAudio(filename):
  pygame.mixer.init()
  pygame.mixer.music.load(filename)
  pygame.mixer.music.play()
  while pygame.mixer.music.get_busy() == True:
    time.sleep(0.01)
	 
def init_pir_pins():
	global PIR_PINS
	for key in PINS_IN.keys():
		pir_idx = 0
		try:
			pir_idx = key.index("pir")
		except ValueError:
			pir_idx = -1
		if pir_idx == 0:
			PIR_PINS.append(PINS_IN[key])

def init_pins():
	for v in PINS_IN.values():
		GPIO.setup(v, GPIO.IN)
		
	for v in PINS_OUT.values():
		GPIO.setup(v, GPIO.OUT)
		
lastLedColor = None
color_fade = True
colorTo = [0, 0, 0]
colorFrom = [0, 0, 0]
steps = .1

def Lerp(a, b, f) :
  return a + f * (b - a)

def colorFadeTick():
	global color_fade, rPWM, gPWM, bPWM, colorTo, colorFrom, steps
	if color_fade:
		colorFrom[0] = Lerp(colorFrom[0], colorTo[0], steps)		
		colorFrom[1] = Lerp(colorFrom[1], colorTo[1], steps)		
		colorFrom[2] = Lerp(colorFrom[2], colorTo[2], steps)
		r = colorFrom[0]
		g = colorFrom[1]
		b = colorFrom[2]
		time.sleep(0.05)
	else:
		r = colorTo[0]
		g = colorTo[1]
		b = colorTo[2]
		
	#print "Set led color to: %s:%s:%s" % (r, g, b), colorFrom, colorTo
	rPWM.ChangeDutyCycle(r)
	gPWM.ChangeDutyCycle(g)
	bPWM.ChangeDutyCycle(b)

def setLedColor(hexStr):
	global rPWM, gPWM, bPWM, lastLedColor, colorTo
	if lastLedColor != hexStr:
		lastLedColor = hexStr
		rgb = struct.unpack('BBB', hexStr.decode('hex'))
		colorTo[0] = (rgb[0] / 255.0) * 100
		colorTo[1] = (rgb[1] / 255.0) * 100
		colorTo[2] = (rgb[2] / 255.0) * 100
	
rainbow_tick_idx = 0
rainbow_tick_timestamp = 0
rainbow_tick_status = 0
def rainbow_tick():
	global rainbow_tick_idx, rainbow_tick_status, rainbow_tick_timestamp, steps
	rainbow_tick_status = (rainbow_tick_status + 1) % 2
	if rainbow_tick_status == 1:
		randomColor = ['A8032D', '4DB1DB', '6CDB4D']
		rainbow_tick_idx = (rainbow_tick_idx + 1) % len(randomColor)
		randomColor = randomColor[rainbow_tick_idx]
		setLedColor(randomColor)
		rainbow_tick_timestamp = time.time() + 2
	else:
		setLedColor('000000')
		rainbow_tick_timestamp = time.time() + 1
			
def checkPirs():
	global color_fade, rainbow_tick_timestamp
	triggered_count = 0	
	idx = 0
	for pin in PIR_PINS:
		i = GPIO.input(pin)
		print "%d triggered: %d" % (idx, i == 1)
		if i == 1:
			triggered_count += 1
		idx += 1
			
	color_fade = False
	if triggered_count == 4:
		if time.time() > rainbow_tick_timestamp:
			rainbow_tick()	
	if triggered_count == 0:
		setLedColor('000000')
	if triggered_count == 1:
		setLedColor('A8032D')
	if triggered_count == 2:
		setLedColor('4DB1DB')
	if triggered_count == 3:
		setLedColor('6CDB4D')
		
	time.sleep(1)
							
def loop():
	while True:
		checkPirs()
		colorFadeTick()
		
init_pins()
rPWM, gPWM, bPWM = init_led_pins()
init_pir_pins()

try:
	loop()
finally:
	GPIO.cleanup()
