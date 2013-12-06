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
import psycopg2
import psycopg2.extras

mesosite = psycopg2.connect(database='mesosite', host='iemdb', user='nobody')
cursor = mesosite.cursor(cursor_factory=psycopg2.extras.DictCursor)

os.chdir(secret.BASE)
sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")


# Which webcam, establish existing lat/lon and pan0
cid = sys.argv[1]
network = cid[:4]

# Get db info
cursor.execute("""
 SELECT ST_x(geom) as lon, ST_y(geom) as lat, * from webcams where id = %s
""", (cid,))

row = cursor.fetchone()
row = dict(row)
clat = row['lat']
clon = row['lon']
newpan0 = row['pan0'] + int(sys.argv[2])
print 'Webcam %s initial pan0: %s attempting: %s' % (cid, row['pan0'], newpan0 )
print "UPDATE webcams SET pan0 = %s WHERE id = '%s';" % (newpan0, cid)
row['pan0'] = newpan0
if row["is_vapix"]:
    camera = vbcam.VAPIX(cid, row, secret.vbcam_user[network], 
                     secret.vbcam_pass[network])
else:
    camera = vbcam.vbcam(cid, row, secret.vbcam_user[network], 
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
print camera.panDrct(azimuth)
time.sleep(5)

# Get still image
buf = StringIO.StringIO()
buf.write( camera.getOneShot() )
buf.seek(0)
i0 = Image.open( buf )

# Draw crosshairs and other info
draw = ImageDraw.Draw(i0)
# x y
draw.rectangle( [316,218,324,262], fill="#FFFFFF" )
draw.rectangle( [298,244,342,236], fill="#FFFFFF" )
draw.rectangle( [318,220,322,260], fill="#000000" )
draw.rectangle( [300,242,340,238], fill="#000000" )

# Save image!
i0.save('cal.jpg')
del i0
del buf
camera.closeConnection()
