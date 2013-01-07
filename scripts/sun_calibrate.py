"""
 Something to calibrate the location of the webcam and direction!
"""
import secret
import time
import sys
import math
import StringIO
import os
import ephem
import mx.DateTime
import Image
import ImageDraw
import pg
mesosite = pg.connect('mesosite', host=secret.DBHOST, user='nobody')


os.chdir(secret.BASE)
sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")


# Which webcam, establish existing lat/lon and pan0
cid = sys.argv[1]
network = cid[:4]

# Get db info
rs = mesosite.query(""" SELECT x(geom) as lon, y(geom) as lat, *
 from webcams where id = '%s'
""" % (cid,)).dictresult()


clat = rs[0]['lat']
clon = rs[0]['lon']
rs[0]['pan0'] = int(rs[0]['pan0']) + int(sys.argv[2])
camera = vbcam.vbcam(cid, rs[0], secret.vbcam_user[network], 
                     secret.vbcam_pass[network])

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
time.sleep(5)

# Get still image
buf = StringIO.StringIO()
buf.write( camera.getOneShot() )
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
