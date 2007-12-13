#!/usr/bin/env python

from secret import *

import sys, os
import ephem
import math
import time
import mx.DateTime
from pyIEM import cameras
from PIL import Image, ImageDraw, ImageFont
import StringIO
import logging

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")



font = ImageFont.truetype(BASE+'lib/LTe50874.ttf', 22)
cid = sys.argv[1]
network = cid[:4]
body = sys.argv[2]
delay = float(sys.argv[3])

dir = "tracker.%s.%s" % (cid, mx.DateTime.now().strftime("%Y%m%d%H%M%S"))
os.makedirs(dir)
os.chdir(dir)
logging.basicConfig(filename="%s.log"%(cid,),filemode='w', level=logging.DEBUG)

if (body.lower() == "sun"):
    body = ephem.Sun()
    logging.debug("Tracking the sun!")
else:
    body = ephem.Moon()
    logging.debug("Tracking the moon!")


cam = vbcam.vbcam(cid, cameras.cams[cid], vbcam_user[network], vbcam_pass[network] )

here = ephem.Observer()
here.long, here.lat = str(cameras.cams[cid]['lon']), str(cameras.cams[cid]['lat'])

cam.zoom(30.0)
cam.getSettings()
#print cam.settings
cam.tilt(0)

stepi = 0
while (1):

    gmt = mx.DateTime.gmt()
    here.date = gmt.strftime('%Y/%m/%d %H:%M:%S')
    body.compute( here )
    azimuth = float(body.az) * 360.0/(2*math.pi)
    alt = float(body.alt) * 360.0/(2*math.pi)
    logging.debug("%s AZ: %.4f AL: %.4f" % (gmt, azimuth, alt) )
    if (alt < -5):
        time.sleep(delay)
        continue

    cam.panDrct(azimuth)
    #cam.tilt(float(alt) + 2.0)
    #cam.tilt(float(alt))
    drct = cam.getDirection()


    # Create buffer
    buf = StringIO.StringIO()
    buf.write( cam.getStillImage() )
    buf.seek(0)
    i0 = Image.open( buf )

    now = mx.DateTime.now()
    str = "%s   %s" % (cam.drct2txt(drct), now.strftime("%-I:%M %p") )
    (w, h) = font.getsize(str)

    draw = ImageDraw.Draw(i0)
    draw.rectangle( [75,370,205,370+h], fill="#000000" )
    draw.rectangle( [318,238,322,242], fill="#000000" )
    draw.text((200-w,370), str, font=font)
    str2 = "%s %s" % (body.az, body.alt)
    (w, h) = font.getsize(str2)
    #draw.rectangle( [320,250,550,250+h], fill="#000000" )
    #draw.text((550-w,250), str2, font=font)
    del draw

    i0.save('%05i.jpg' % (stepi,))
    del i0
    del buf
    time.sleep(delay)

    stepi += 1
