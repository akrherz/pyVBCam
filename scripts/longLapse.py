import secret

import httplib, re, time, logging
import StringIO, mx.DateTime
from PIL import Image, ImageDraw, ImageFont
import sys, os
import pg

db = pg.connect('mesosite', host=secret.DBHOST)


sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("%s/tmp/" % (secret.BASE,))

site = sys.argv[1]
network = site[:4]

dir = "longterm.%s.%s" % (site, mx.DateTime.now().strftime("%Y%m%d%H%M%S"))
os.makedirs(dir)
os.chdir(dir)

logging.basicConfig(filename="%s.log"%(site,),filemode='w' )

password = secret.vbcam_pass[network]
user = secret.vbcam_user[network]
if secret.vbcam_user.has_key(site):
    password = secret.vbcam_pass[site]
    user = secret.vbcam_user[site]

rs = db.query("""SELECT * from webcams where id = '%s'""" % (site,)).dictresult()
db.close()

c = vbcam.vbcam(site, rs[0], user, password)
logging.info("Camera Settings: %s" % ( c.settings, ) )

font = ImageFont.truetype(secret.BASE+'lib/veramono.ttf', 22)
#c.panDrct(335)

#dirs = [0, 45, 90, 135, 180, 225, 270, 315, 360, 45, 90]
i = 0
while i < 100000:
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
    str = "%3s %8s" % (vbcam.drct2dirTxt(drct), now.strftime("%-I:%M %p") )
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
