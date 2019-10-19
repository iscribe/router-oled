#!/usr/bin/python3

import os
import sys

import calendar
import time

import logging as log
import RPi.GPIO as GPIO


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import speedtest

import lte_stats

GND	= 18
RED     = 17
GREEN   = 27
BLUE    = 22

OFF     = GPIO.HIGH
ON      = GPIO.LOW

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(GND, GPIO.OUT)
GPIO.setup(RED, GPIO.OUT)
GPIO.setup(GREEN, GPIO.OUT)
GPIO.setup(BLUE, GPIO.OUT)

GPIO.output(RED, ON)
GPIO.output(GREEN, OFF)
GPIO.output(BLUE, OFF)


disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
disp.begin()
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
line1 = "ROUTER"
line2 = "INITIALISING"
x = 64 - (len(line1) * 3)
y = 8
draw.text((x, y), line1, fill=255)
x = 64 - (len(line2) * 3)
y = 16
draw.text((x, y), line2, fill=255)

disp.image(image)
disp.display()
