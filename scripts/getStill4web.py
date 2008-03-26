#!/usr/bin/env python
# Get still image for the website mostly

from secret import *

import logging

from pyIEM import cameras
import pg
db = pg.connect('mesosite', host=DBHOST)

from twisted.internet import reactor
#reactor.suggestThreadPoolSize(40)

import StringIO, mx.DateTime, os, sys
from PIL import Image, ImageDraw, ImageFont

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")



def camRunner( cid ):
# Who am I running for
  d = cameras.cams[cid]
  if (not d['online']):
    return

  password = vbcam_pass['KCCI']
  if (cid[:4] == "KELO"):
    password = vbcam_pass['KELO']
  cam = vbcam.vbcam(cid, d, 'root', password, logLevel=logging.INFO)
  cam.retries = 2

  # Get Still
  buf = StringIO.StringIO()
  buf.write( cam.getOneShot() )
  buf.seek(0)
  if (buf.len == 0):
    return
  i0 = Image.open( buf )
  # 320x240 variant
  i320 = i0.resize((320, 240), Image.ANTIALIAS) 

  # Get direction cam is looking
  drct = cam.getDirection() 
  drctTxt = cam.drct2txt( drct )
  
  # Place timestamp/direction on image
  font = ImageFont.truetype(BASE+'/lib/veramono.ttf', 10)
  now = mx.DateTime.now()
  gmt = mx.DateTime.gmt()

  draw = ImageDraw.Draw(i0)
  str = "(%s) %s %s" % (drctTxt, d['name'], now.strftime("%-2I:%M:%S %p - %d %b %Y") )
  (w, h) = font.getsize(str)
  draw.rectangle( [5,475-h,5+w,475], fill="#000000" )
  draw.text((5,475-h), str, font=font)

  # Save 640x480
  i0.save("%s-640x480.jpg" % (cid,) )

  draw = ImageDraw.Draw(i320)
  str = "(%s) %s %s" % (drctTxt, d['name'], now.strftime("%-2I:%M:%S %p - %d %b %Y") )
  (w, h) = font.getsize(str)
  draw.rectangle( [5,235-h,5+w,235], fill="#000000" )
  draw.text((5,235-h), str, font=font)

  # Save 640x480
  i320.save("%s-320x240.jpg" % (cid,) )

  # Save direction to database
  sql = "INSERT into camera_log(cam, valid, drct) values ('%s','%s',%s)" %\
     (cid, now.strftime('%Y-%m-%d %H:%M'), drct)
  db.query(sql)


  sql = "DELETE from camera_current WHERE cam = '%s'" % (cid,)
  db.query(sql)

  sql = "INSERT into camera_current(cam, valid, drct) values ('%s','%s',%s)" \
   %(cid, now.strftime('%Y-%m-%d %H:%M'), drct)
  db.query(sql)

  # Put into LDM
  cmd = "/home/ldm/bin/pqinsert -p 'webcam ac %s camera/stills/%s.jpg camera/%s/%s_%s.jpg jpg' %s-320x240.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid, cid, gmt.strftime("%Y%m%d%H%M"), cid)
  os.system(cmd)
  cmd = "/home/ldm/bin/pqinsert -p 'webcam c %s camera/640x480/%s.jpg bogus jpg' %s-640x480.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid )
  os.system(cmd)

  # Upload to website!
  if (cid[:4] == "KELO"):
    n = int(cid[5:])
    cmd = "lftp -e 'put %s-640x480.jpg -o cam%s.jpg; quit' -u %s" % (cid, n, kelo_ftp_str)
    os.system(cmd)

  slaughter()

def slaughter():
  os.kill(os.getpid(), 9)

cid = sys.argv[1]
reactor.callInThread( camRunner, cid )

# You have 1 minute to finish :)
reactor.callLater(57, slaughter)

# Go reactor
reactor.run()
