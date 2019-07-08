from PIL import Image, ImageDraw, ImageFont
import BHack_ILI9225 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import sys, time, os
import numpy as np
import Adafruit_BBIO.ADC as ADC

# BeagleBone Black configuration.
RS = 'P9_15'
RST = 'P9_12'
SPI_PORT = 1
SPI_DEVICE = 0
# SPI0_CS0 = P9_17
# SPI0_SLCK = P9_22
# SPI0_D1 (MOSI) = P9_18

# Create TFT LCD display class.
disp = TFT.ILI9225(RS, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))

size = (220, 176)
ADC.setup()
# Initialize display.
disp.begin()
disp.clear()
img = [[1,1]]
x = []
y = []

im = Image.new('L', (176, 220), 255)
imgdata = np.array(img[0][1])*256 + np.array(img[0][1])
draw = ImageDraw.Draw(im)


burstTime = time.time()
draw.line(list(zip(x, y)), fill=0, width=2)  # Draws entire line.
disp.display(im)

def setYRange(points):
	for i in range(0, 220, points):
		y.append(i)
	#print ("y = ", y)
samplesToCapture = 20
setYRange(samplesToCapture)

while (True):
	
	img = Image.new('L', (176, 220), 255)
	drawImg = ImageDraw.Draw(img)
	value = (ADC.read("P9_40"))
	value = int(round(value * 100))
	x.append(value)
	#print(x)
	if len(x) == samplesToCapture:
		nowTime = time.time()
		#print (nowTime - burstTime)
		drawImg.line(list(zip(x, y)), fill=0, width=2)
		disp.display(img)
		#print (time.time() - nowTime)
		print ("X = ",x)
		x = []
		burstTime = nowTime
		



