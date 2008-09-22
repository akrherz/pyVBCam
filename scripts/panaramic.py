#!/usr/bin/env python

from secret import *

import sys, math, StringIO, os, time
import ephem, mx.DateTime
from PIL import Image, ImageDraw
from pyIEM import cameras

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")


# Which webcam, establish existing lat/lon and pan0
cid = sys.argv[1]
network = cid[:4]
camera = vbcam.vbcam(cid, cameras.cams[cid], vbcam_user[network], vbcam_pass[network])
camera.zoom(40.0)
out = Image.new('RGB', (720,480) )

i = 0
for ang in range(-160,180,40):
  print "Working on Angle: %s" % (ang,)
  camera.pan( ang )
  time.sleep(2) # Settle down the cam
  o = open("tmp.jpg", 'w')
  o.write( camera.getStillImage() )
  o.close()

  i0 = Image.open("tmp.jpg")
  i02 = i0.resize( (124,240) )
  row = int(i/5)
  col = i%5
  out.paste(i02, (124*col,row*240) )
  if (i == 4):
    i = 5
    row = int(i/5)
    col = i%5
    out.paste(i02, (124*col,row*240) )
  del i0, i02
  i += 1

out.save("test.jpg")
del out
