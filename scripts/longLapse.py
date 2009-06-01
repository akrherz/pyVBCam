#!/usr/bin/env python

from secret import *

import httplib, re, time, logging
import StringIO, mx.DateTime
from pyIEM import mesonet, cameras
from PIL import Image, ImageDraw, ImageFont
import sys, os

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")

site = sys.argv[1]
network = site[:4]

dir = "longterm.%s.%s" % (site, mx.DateTime.now().strftime("%Y%m%d%H%M%S"))
os.makedirs(dir)
os.chdir(dir)

logging.basicConfig(filename="%s.log"%(site,),filemode='w' )

password = vbcam_pass[network]
user = vbcam_user[network]
if vbcam_user.has_key(site):
    password = vbcam_pass[site]
    user = vbcam_user[site]

c = vbcam.vbcam(site, cameras.cams[site], user, password)
logging.info("Camera Settings: %s" % ( c.settings, ) )

font = ImageFont.truetype(BASE+'lib/veramono.ttf', 22)
#c.panDrct(335)

#dirs = [0, 45, 90, 135, 180, 225, 270, 315, 360, 45, 90]
i = 0
while (i < 100000):
    logging.info("i = %s" % (i,) )

    # Set up buffer for image to go to
    buf = StringIO.StringIO()

    #c.panDrct(90 + (.25 * i))
    #c.panDrct( dirs[i] )
    drct = c.getDirection()
    buf.write( c.getOneShot() )
    buf.seek(0)
    i0 = Image.open( buf )

    now = mx.DateTime.now()
    str = "%3s %8s" % (mesonet.drct2dirTxt(drct), now.strftime("%-I:%M %p") )
    (w, h) = font.getsize(str)

    draw = ImageDraw.Draw(i0)
    draw.rectangle( [215-w-10,370,215,370+h], fill="#000000" )
    draw.text((210-w,370), str, font=font)
    del draw


    i0.save('%05i.jpg' % ( i,))
    del i0
    del buf
    time.sleep(int(sys.argv[2]))
    i += 1

