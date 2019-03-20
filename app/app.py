#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image, ImageFont
import datetime
import inkyphat
import os
import requests
import signal
import sys
import threading
import time

def signal_handler(signal, frame):
    print("\nprogram exiting gracefully")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# from env
DS_KEY = os.getenv('DS_KEY')
if DS_KEY == None:
    print 'DS_KEY env var not set'
    sys.exit
DS_UNITS = os.getenv('DS_UNITS', 'uk2')
DS_LAT_LNG = os.getenv('DS_LAT_LNG', '50.821,-0.151')
ROTATE_180 = os.getenv('ROTATE_180', 'false') == 'true'

NUM_COLS = 5
COL_WIDTH = inkyphat.WIDTH / NUM_COLS
COL_TIME_INCREMENT = 3 # hours
FONT_PATH = 'assets/roboto.ttf'

# setup fonts
timeFont = ImageFont.truetype(FONT_PATH, 14)
temperatureFont = ImageFont.truetype(FONT_PATH, 20)
summaryFont = ImageFont.truetype(FONT_PATH, 12)

def get_x(width, col):
    return (COL_WIDTH / 2) - (width / 2) + (col * COL_WIDTH)

def convert_ds_hour(dsHour):
    time = '{:%H:%M}'.format(datetime.datetime.fromtimestamp(dsHour['time']))
    icon = dsHour['icon']
    temperature = '{0:.0f}'.format(dsHour['temperature']) + u"\u00b0"
    return {'time': time, 'icon': icon, 'temperature': temperature}

def get_weather():
    try:
        p = {'exclude': 'minutely,daily,alerts,flags', 'units': DS_UNITS }
        r = requests.get('https://api.darksky.net/forecast/' + DS_KEY + '/' + DS_LAT_LNG, params=p)
        body = r.json()

        dsHours = body['hourly']['data']
        hours = []
        for i in range(0, NUM_COLS):
            hours.append(convert_ds_hour(dsHours[i * COL_TIME_INCREMENT]))

        return {'summary': body['hourly']['summary'], 'hours': hours}
    except:
        return None

def draw_weather():
    weather = get_weather()
    if weather == None:
        print 'No weather!'
        return


    if ROTATE_180 == True:
        inkyphat.set_rotation(180)
    # TODO configurable color
    inkyphat.set_colour('red')
    inkyphat.set_border(inkyphat.RED)

    # background
    inkyphat.rectangle((0, 0, inkyphat.WIDTH, inkyphat.HEIGHT), inkyphat.RED)

    # draw columns
    # (assuming get_weather has returned using NUM_COLS)
    for i in range(0, NUM_COLS):
        # draw time label
        time = weather['hours'][i]['time']
        w, h = timeFont.getsize(time)
        inkyphat.text((get_x(w, i), 4), time, inkyphat.WHITE, font = timeFont)

        # draw icon
        try:
            # This could be optimized to not load the same file more than once
            img = Image.open('assets/' + weather['hours'][i]['icon'] + '.png')
            inkyphat.paste(img, (get_x(30, i), 22))
            # drawing icons without transparency as it didn't work with whatever gimp was producing
        except:
            print 'Error with icon:' + weather['hours'][i]['icon']

        # draw temperature label
        temp = weather['hours'][i]['temperature']
        w, h = temperatureFont.getsize(temp)
        inkyphat.text((get_x(w, i), 56), temp, inkyphat.WHITE, font=temperatureFont)

    inkyphat.text((5, 84), weather['summary'], inkyphat.WHITE, font=summaryFont)

    inkyphat.show()

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

while True:
    run_threaded(draw_weather)
    now = datetime.datetime.now()
    secondsToNextHour = (59 - now.minute) * 60 + (60 - now.second)
    #secondsToNextHour = (60 - now.second) # run once per minute for developing
    time.sleep(secondsToNextHour)

