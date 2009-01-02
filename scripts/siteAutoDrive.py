#!/usr/bin/env python

from secret import *

import httplib, re, time, logging
import StringIO, mx.DateTime
from pyIEM import mesonet, cameras
from PIL import Image, ImageDraw, ImageFont
import sys, os, shutil, random

from pyxmpp.jid import JID
from pyxmpp.jabber.simple import send_message

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")


init_delay = int(sys.argv[1])
site = sys.argv[2]
network = site[:4]
secs = int(float(sys.argv[3]))
filename = sys.argv[4]
movie_duration = int(float(sys.argv[5]))

# Initially sleep until it is go time!
time.sleep(init_delay + random.random() )

# compute
sts = mx.DateTime.now()
ets = sts + mx.DateTime.RelativeDateTime(seconds = secs)

dir = ("autoframes.%s_%s" % (filename, mx.DateTime.now())).replace(" ", "_")

os.makedirs(dir)
os.chdir(dir)

logging.basicConfig(filename="%s.log"%(site,),filemode='w' )

dateHT = 370
isKELO = False
isKCRG = False
if (network == "KELO"):
  isKELO = True
if (network == "KCRG"):
  isKCRG = True

c = vbcam.vbcam(site, cameras.cams[site], vbcam_user[network], vbcam_pass[network])

logging.info("Camera Settings: %s" % ( c.settings, ) )

font = ImageFont.truetype('../../lib/veramono.ttf', 22)
sfont = ImageFont.truetype('../../lib/veramono.ttf', 14)

i = 0
frames = movie_duration * 30
while (i < frames ):
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

    draw = ImageDraw.Draw(i0)

    if (not isKELO):
      str = "%s   %s" % (mesonet.drct2dirTxt(drct), now.strftime("%-I:%M %p") )
      (w, h) = font.getsize(str)
      if (isKCRG):
        draw.rectangle( [545-w-10,dateHT,545,dateHT+h], fill="#000000" )
        draw.text((540-w,dateHT), str, font=font)
      else:
        draw.rectangle( [205-w-10,dateHT,205,dateHT+h], fill="#000000" )
        draw.text((200-w,dateHT), str, font=font)

      str = "%s" % (now.strftime("%d %b %Y"), )
    else:
      str = "%s  %s" % (now.strftime("%d %b %Y %-I:%M %p"), mesonet.drct2dirTxt(drct))
    (w, h) = sfont.getsize(str)
    draw.rectangle( [0,480-h,0+w,480], fill="#000000" )
    draw.text((0,480-h), str, font=sfont)
    del draw


    i0.save('%05i.jpg' % ( i,))
    del i0
    del buf
    secs_left = (ets - mx.DateTime.now()).seconds
    delay = (secs_left -((frames -i) * 2)) / (frames - i) 
    logging.info("secs_left = %s, frames_left = %s, delay = %s" % (secs_left, frames-i, delay,))
    if (delay < 0): delay = 0
    time.sleep(delay)
    i += 1

# Lets sleep for around 6 minutes, so that we don't have 27 ffmpegs going 
time.sleep( 360. * random.random() )

# Create something for KCCI
os.system("ffmpeg -i %05d.jpg -b 2000k out.mov < /dev/null >& /dev/null")
os.system("/home/ldm/bin/pqinsert -p 'lapse c %s %s/%s.qt BOGUS qt' out.mov" % (sts.strftime("%Y%m%d%H%M"), network, filename) )

# Create something for website
os.system("ffmpeg -i %05d.jpg -s 320x240 -vcodec wmv1 out.wmv < /dev/null >& /dev/null")
shutil.copyfile("out.wmv", "/mesonet/share/lapses/auto/%s.wmv" % (filename,) )

# Create Flash Video in full res!
os.system("ffmpeg -i %05d.jpg -b 1000k out.flv < /dev/null >& /dev/null")
shutil.copyfile("out.flv", "/mesonet/share/lapses/auto/%s.flv" % (filename,) )

# Create tar file of images
os.system("tar -cf %s_frames.tar *.jpg" % (filename,) )
shutil.copyfile("%s_frames.tar" % (filename,), "/mesonet/share/lapses/auto/%s_frames.tar" % (filename,))

jabberTxt = "Webcam scheduler done! delivered %s.qt" % (filename,)
bare = "akrherz@iemchat.com/alert_%s" %(mx.DateTime.now().ticks(),)
jid=JID(bare)
recpt=JID('kcci_wx2@iemchat.com')
#send_message(jid,'hello',recpt,jabberTxt,'Ba')
