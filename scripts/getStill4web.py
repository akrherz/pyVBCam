# Get still image for the website mostly

import secret
import logging
import pg
from twisted.internet import reactor
import StringIO, mx.DateTime, os, sys
from PIL import Image, ImageDraw, ImageFont

db = pg.connect('mesosite', host=secret.DBHOST)

#reactor.suggestThreadPoolSize(40)

sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("%s/tmp/" % (secret.BASE,))



def camRunner( cid ):
# Who am I running for
    rs = db.query("""SELECT * from webcams where id = '%s' """ % (cid,)).dictresult()
    row = rs[0]
    network = row['network']
    password = secret.vbcam_pass[network]
    user = secret.vbcam_user[network]
    if secret.vbcam_user.has_key(cid):
        password = secret.vbcam_pass[cid]
        user = secret.vbcam_user[cid]
    cam = vbcam.vbcam(cid, row, user, password, logLevel=logging.INFO)
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
    font = ImageFont.truetype(secret.BASE+'/lib/veramono.ttf', 10)
    now = mx.DateTime.now()
    gmt = mx.DateTime.gmt()

    draw = ImageDraw.Draw(i0)
    str = "(%s) %s %s" % (drctTxt, row['name'], now.strftime("%-2I:%M:%S %p - %d %b %Y") )
    (w, h) = font.getsize(str)
    draw.rectangle( [5,475-h,5+w,475], fill="#000000" )
    draw.text((5,475-h), str, font=font)

    # Save 640x480
    i0.save("%s-640x480.jpg" % (cid,) )

    draw = ImageDraw.Draw(i320)
    str = "(%s) %s %s" % (drctTxt, row['name'], now.strftime("%-2I:%M:%S %p - %d %b %Y") )
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
    cmd = "/home/ldm/bin/pqinsert -p 'webcam c %s camera/stills/%s.jpg camera/%s/%s_%s.jpg jpg' %s-320x240.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid, cid, gmt.strftime("%Y%m%d%H%M"), cid)
    os.system(cmd)
    cmd = "/home/ldm/bin/pqinsert -p 'webcam ac %s camera/640x480/%s.jpg camera/%s/%s_%s.jpg jpg' %s-640x480.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid, cid, gmt.strftime("%Y%m%d%H%M"), cid )
    os.system(cmd)

  # Upload to website!
  #if (network == "KELO"):
  #  n = int(cid[5:])
  #  cmd = "lftp -e 'put %s-640x480.jpg -o cam%s.jpg; quit' -u %s" % (cid, n, kelo_ftp_str)
  #  os.system(cmd)

    slaughter()

def slaughter():
    db.close()
    os.kill(os.getpid(), 9)

cid = sys.argv[1]
reactor.callInThread( camRunner, cid )

# You have 1 minute to finish :)
reactor.callLater(57, slaughter)

# Go reactor
reactor.run()
