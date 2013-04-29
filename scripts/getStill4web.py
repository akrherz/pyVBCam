"""
 Get still image for the website mostly
"""
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

from twisted.internet import reactor
import StringIO
import os
import subprocess
import sys
import datetime
import urllib2
import logging
from PIL import Image, ImageDraw, ImageFont
import pytz
import psycopg2
import psycopg2.extras
dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (config.get('database', 'host'),
                                              config.get('database', 'user'),
                                              config.get('database', 'name')))
cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

sys.path.insert(0, "../vbcam")
import vbcam

def camRunner( cid ):
# Who am I running for
    cursor.execute("""SELECT * from webcams where id = %s """, (cid,))
    row = cursor.fetchone()
    now = datetime.datetime.now()
    now = now.replace(tzinfo=pytz.timezone("America/Chicago"))
    gmt = datetime.datetime.utcnow()
    network = row['network']
    if row['scrape_url'] is None:
        password = config.get(network, 'password')
        user = config.get(network, 'user')
        if config.has_section(cid):
            password = config.get(cid, 'password')
            user = config.get(cid, 'user')
        cam = vbcam.vbcam(cid, row, user, password, logLevel=logging.INFO)
        cam.retries = 2

        # Get Still
        buf = StringIO.StringIO()
        buf.write( cam.getOneShot() )
        buf.seek(0)

    else:
        url = row['scrape_url']
        req = urllib2.Request(url)
        try:
            req2 = urllib2.urlopen(req)
        except Exception, exp:
            if now.minute == 0:
                print 'Exception for %s: %s' % (cid, exp)
            return
        modified = req2.info().getheader('Last-Modified')
        if modified:
            gmt = datetime.datetime.strptime(modified, "%a, %d %b %Y %H:%M:%S %Z")
            now = gmt + datetime.timedelta(seconds=now.utcoffset().seconds)
            # Round up to nearest 5 minute bin
            roundup = 5 - now.minute % 5
            gmt += datetime.timedelta(minutes=roundup)
        buf = StringIO.StringIO( req2.read() )
        buf.seek(0)
    if buf.len == 0:
        return
    i0 = Image.open( buf )
    # 320x240 variant
    try:
        i320 = i0.resize((320, 240), Image.ANTIALIAS) 
    except:
        slaughter()
        return

    # Get direction cam is looking
    if row['scrape_url'] is None:
        drct = cam.getDirection() 
        drctTxt = cam.drct2txt( drct )
    else:
        drct = row['pan0']
        drctTxt = vbcam.drct2dirTxt( row['pan0'] )
  
    # Place timestamp/direction on image
    font = ImageFont.truetype('../lib/veramono.ttf', 10)


    draw = ImageDraw.Draw(i0)
    text = "(%s) %s %s" % (drctTxt, row['name'], 
                          now.strftime("%-2I:%M:%S %p - %d %b %Y") )
    (w, h) = font.getsize(text)
    draw.rectangle( [5,475-h,5+w,475], fill="#000000" )
    draw.text((5,475-h), text, font=font)

    # Save 640x480
    i0.save("../tmp/%s-640x480.jpg" % (cid,) )

    draw = ImageDraw.Draw(i320)
    text = "(%s) %s %s" % (drctTxt, row['name'], now.strftime("%-2I:%M:%S %p - %d %b %Y") )
    (w, h) = font.getsize(text)
    draw.rectangle( [5,235-h,5+w,235], fill="#000000" )
    draw.text((5,235-h), text, font=font)

    # Save 640x480
    i320.save("../tmp/%s-320x240.jpg" % (cid,) )

    # Save direction to database
    sql = "INSERT into camera_log(cam, valid, drct) values (%s,%s,%s)"
    args = (cid, now.strftime('%Y-%m-%d %H:%M'), drct)
    cursor.execute(sql, args)


    sql = "DELETE from camera_current WHERE cam = %s"
    args = (cid,)
    cursor.execute(sql, args)

    sql = "INSERT into camera_current(cam, valid, drct) values (%s,%s,%s)"
    args = (cid, now.strftime('%Y-%m-%d %H:%M'), drct)
    cursor.execute(sql, args)

    # Put into LDM
    cmd = "/home/ldm/bin/pqinsert -p 'webcam c %s camera/stills/%s.jpg camera/%s/%s_%s.jpg jpg' ../tmp/%s-320x240.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid, cid, gmt.strftime("%Y%m%d%H%M"), cid)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    proc.stderr.read()
    cmd = "/home/ldm/bin/pqinsert -p 'webcam ac %s camera/640x480/%s.jpg camera/%s/%s_%s.jpg jpg' ../tmp/%s-640x480.jpg" % (gmt.strftime("%Y%m%d%H%M"), cid, cid, cid, gmt.strftime("%Y%m%d%H%M"), cid )
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    proc.stderr.read()

    slaughter()

def slaughter():
    cursor.close()
    dbconn.commit()
    dbconn.close()
    killer()
    
def killer():
    os.kill(os.getpid(), 9)

def eb():
    pass

cid = sys.argv[1]
reactor.callInThread( camRunner, cid )

# You have 1 minute to finish :)
reactor.callLater(57, slaughter)
reactor.callLater(59, killer)

# Go reactor
reactor.run()
