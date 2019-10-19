#!/usr/bin/python3

import os
import sys

import calendar
import time

import logging as log
import RPi.GPIO as GPIO

from uuid import getnode

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

import paho.mqtt.client as mqtt

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

PAD = -2

MQTT_HOST = "192.168.2.200"


def setled(pin):
	GPIO.output(RED, OFF)
	GPIO.output(GREEN, OFF)
	GPIO.output(BLUE, OFF)
	GPIO.output(pin, ON)


def draw_signal(i, signalStrength=0):
	draw = ImageDraw.Draw(i)
	x = 116
	signalStrength = int(signalStrength)

	if(signalStrength < 1):
		pass

	if(signalStrength >= 1):
		draw.line((x, 6, x, 5), fill=255)

	if(signalStrength >= 2):
                draw.line((x+3, 6, x+3, 4), fill=255)

	if(signalStrength >= 3):
                draw.line((x+6, 6, x+6, 3), fill=255)

	if(signalStrength >= 4):
                draw.line((x+9, 6, x+9, 2), fill=255)

	if(signalStrength >= 5):
                draw.line((x+12, 6, x+12, 1), fill=255)

	return i

def draw_sms(i, messages):
	draw = ImageDraw.Draw(i)
	x = 110
	y = 25
	draw.rectangle((x, y, x+17, y+6), outline=255, fill=0)
	draw.line((x,y,x+9,y+3), fill=255)
	draw.line((x+17,y,x+9,y+3), fill=255)
	txt_x = x - ((len(messages) * 7) + 2)
	draw.text((txt_x, y-2), str(messages), fill=255)
	return i

def draw_carrier(i, provider, signalType):
	draw = ImageDraw.Draw(i)
	draw.text((0, PAD), "{} {}".format(provider, signalType), fill=255)

	return i

def draw_status(i, status):
	draw = ImageDraw.Draw(i)
	x = 64 - (len(status) * 3)
	y = 10
	draw.text((x, y), status, fill=255)
	return i

def draw_speed(i, upload=0, download=0):
    draw = ImageDraw.Draw(i)
    x = 0
    y = 22

#	cacheTimeout = 300
#	cacheFile = "/tmp/speedTestCache.txt"
#	result_string = None
#
#	if os.path.isfile(cacheFile):
#		fileage = int(calendar.timegm(time.gmtime())) - int(os.stat(cacheFile).st_ctime)
#	else:
#		fileage = 9999999999
#
#	if fileage > cacheTimeout:
#		s = speedtest.Speedtest()
#		s.get_servers([])
#		s.get_best_server()
#		s.download(threads=None)
#		s.upload(threads=None)
#		result = s.results.dict()
#		print(result)

    speed_string = "{}d {}u".format(
        round((float(download) / 1000 / 1000), 1), 
        round((float(upload) / 1000 / 1000), 1))

#        with open(cacheFile, "w") as f:
#			f.write(result_string)

#	else:
#		with open(cacheFile) as f:
#			result_string = f.read()
    draw.text((x, y), speed_string, fill=255)
    return i

def draw_dongleerror(i):
	draw = ImageDraw.Draw(i)
	line1 = "DONGLE"
	line2 = "ERROR"
	x = 64 - (len(line1) * 3)
	y = 8
	draw.text((x, y), line1, fill=255)
	x = 64 - (len(line2) * 3)
	y = 16
	draw.text((x, y), line2, fill=255)
	return i

def main():
    node_id = "oled-{0:x}".format(getnode())

    try:
        client = mqtt.Client(node_id)
        client.connect(MQTT_HOST, port=1883, keepalive=60, bind_address="")
    except Exception as e:
        print("Error connecting to MQTT: {}".format(e))

    disp = Adafruit_SSD1306.SSD1306_128_32(rst=None)
    disp.begin()
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    try:
        data = lte_stats.get_dongle_info()
    except Exception as e:
        print(e)
        data = None


    if data:
        for i in data:
            log.info("{}:{}".format(i, data[i]))
            if client:
                client.publish("/{}/{}".format("4ginternet", i), payload=data[i])
				
        font = ImageFont.load_default()

	#draw = ImageDraw.Draw(image)
	#draw.rectangle((0,0,width,height), outline=0, fill=0)

        image = draw_signal(image, data['SignalStrength'])
        image = draw_carrier(image, data['FullName'], data['CurrentNetworkType'])
        image = draw_sms(image, data['UnreadMessage'])


        if data['ConnectionStatus'] == "Connected" and data['ExternalIPAddress'] != None:
            image = draw_status(image, data['ExternalIPAddress'])
            setled(GREEN)
        elif data['ConnectionStatus'] == "Connecting":
            setled(BLUE)
        else:
            image = draw_status(image, data['ConnectionStatus'])
            setled(RED)

        image = draw_speed(image, data['UploadSpeed'], data['DownloadSpeed'])

        #draw.text((x, top+25), "hello", font=font, fill=255)
    else:
        image = draw_dongleerror(image)

        setled(RED)
        try:
            os.remove("/tmp/ipCacheFile")
            os.remove("/tmp/speedTestCache.txt")
        except:
            pass
	    #draw.text((x, top+25), "", font=font, fill=255)

    disp.image(image)
    disp.display()

if __name__ == "__main__":
    sys.exit(main())
