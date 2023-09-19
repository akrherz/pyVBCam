"""
 Something to calibrate the location of the webcam and direction!
"""
import datetime
import io
import logging
import math
import os
import sys
import time

import ephem
from PIL import Image, ImageDraw
from pyiem.database import get_dbconnc
from pyvbcam import common

logging.basicConfig(level=logging.DEBUG)

mesosite, cursor = get_dbconnc("mesosite")

os.chdir("../tmp")


# Which webcam, establish existing lat/lon and pan0
cid = sys.argv[1]

camera = common.get_vbcam(cid, loglevel=logging.DEBUG)
clat = camera.d["lat"]
clon = camera.d["lon"]
newpan0 = camera.d["pan0"] + int(sys.argv[2])
if newpan0 < 0:
    newpan0 += 360.0
logging.info(
    "Webcam %s initial pan0: %s attempting: %s"
    % (cid, camera.d["pan0"], newpan0)
)
logging.info(
    "\n  UPDATE webcams SET pan0 = %s WHERE id = '%s'; \n" % (newpan0, cid)
)
camera.pan0 = newpan0

# Figure out solar location
sun = ephem.Sun()
here = ephem.Observer()
here.long, here.lat = str(clon), str(clat)
gmt = datetime.datetime.utcnow()
here.date = gmt.strftime("%Y/%m/%d %H:%M:%S")
sun.compute(here)
azimuth = float(sun.az) * 360.0 / (2 * math.pi)

# Point at the sun!
camera.zoom(40)
camera.tilt(0)
logging.info(" Moving the webcam to azimuth: %.1f" % (azimuth,))
camera.panDrct(azimuth)
time.sleep(5)

# Get still image
buf = io.StringIO.StringIO()
buf.write(camera.get_one_shot())
buf.seek(0)
i0 = Image.open(buf)

# Draw crosshairs and other info
draw = ImageDraw.Draw(i0)
# x y
draw.rectangle([316, 218, 324, 262], fill="#FFFFFF")
draw.rectangle([298, 244, 342, 236], fill="#FFFFFF")
draw.rectangle([318, 220, 322, 260], fill="#000000")
draw.rectangle([300, 242, 340, 238], fill="#000000")

# Save image!
i0.save("cal.jpg")
del i0
del buf
camera.closeConnection()
