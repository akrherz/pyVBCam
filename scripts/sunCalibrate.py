#!/usr/bin/env python
# Something to calibrate the location of the webcam and direction!

from secret import *

import sys, math, StringIO, os
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
clat = cameras.cams[cid]['lat']
clon = cameras.cams[cid]['lon']
cameras.cams[cid]['pan0'] += int(sys.argv[2])
camera = vbcam.vbcam(cid, cameras.cams[cid], vbcam_user[network], vbcam_pass[network])

# Figure out solar location
sun = ephem.Sun()
here = ephem.Observer()
here.long, here.lat = str(clon), str(clat)
gmt = mx.DateTime.gmt()
here.date = gmt.strftime('%Y/%m/%d %H:%M:%S')
sun.compute( here )
azimuth = float(sun.az) * 360.0/(2*math.pi)

# Point at the sun!
camera.zoom(40)
camera.tilt(0)
camera.panDrct(azimuth)

# Get still image
buf = StringIO.StringIO()
buf.write( camera.getStillImage() )
buf.seek(0)
i0 = Image.open( buf )

# Draw crosshairs and other info
draw = ImageDraw.Draw(i0)
draw.rectangle( [318,220,322,260], fill="#000000" )
draw.rectangle( [300,242,340,238], fill="#000000" )

# Save image!
i0.save('cal.jpg')
del i0
del buf
camera.closeConnection()
