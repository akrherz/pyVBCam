"""
 Get still image for the website mostly
"""
import datetime
import logging
import subprocess
import sys
import time
from io import BytesIO

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo

import psycopg2.extras
import pyvbcam.utils as camutils
from PIL import Image, ImageDraw, ImageFont
from pyvbcam import vbcam

NOW = datetime.datetime.now().replace(tzinfo=ZoneInfo("America/Chicago"))
FONT = ImageFont.truetype(camutils.DATADIR + "/veramono.ttf", 10)
log = logging.getLogger()
log.setLevel(logging.DEBUG if sys.stdout.isatty() else logging.WARNING)


def get_buffer_and_cam(row, cid, gmt):
    """Get things"""
    if row["scrape_url"] is None:
        cam = vbcam.get_vbcam(cid)
        cam.retries = 2

        # Get Still
        buf = BytesIO()
        buf.write(cam.get_one_shot())
        buf.seek(0)

    else:
        buf, cam = None, None
        # url = row['scrape_url']
        # req = urllib2.Request(url)
        # try:
        #    req2 = urllib2.urlopen(req)
        # except Exception as exp:
        #    if NOW.minute == 0:
        #        print('Exception for %s: %s' % (cid, exp))
        #    return
        # modified = req2.info().getheader('Last-Modified')
        # if modified:
        #    gmt = datetime.datetime.strptime(modified,
        #                                     "%a, %d %b %Y %H:%M:%S %Z")
        #    now = gmt + datetime.timedelta(seconds=NOW.utcoffset().seconds)
        # Round up to nearest 5 minute bin
        #    roundup = 5 - now.minute % 5
        #    gmt += datetime.timedelta(minutes=roundup)
        # buf = StringIO.StringIO(req2.read())
        # buf.seek(0)
    return buf, cam, gmt


def draw_save(cid, img, dirtext, row):
    """Draw and Save Image"""
    (imgwidth, imgheight) = img.size
    draw = ImageDraw.Draw(img)
    text = "(%s) %s %s" % (
        dirtext,
        row["name"],
        NOW.strftime("%-2I:%M:%S %p - %d %b %Y"),
    )
    (width, height) = FONT.getsize(text)

    draw.rectangle(
        [5, imgheight - 5 - height, 5 + width, imgheight - 5], fill="#000000"
    )
    draw.text((5, imgheight - 5 - height), text, font=FONT)

    fn = "../tmp/%s-%.0fx%.0f.jpg" % (cid, imgwidth, imgheight)
    img.save(fn)
    return fn


def do_db(cid, drct):
    """Save direction to database"""
    dbconn = camutils.get_dbconn()
    cursor = dbconn.cursor()
    sql = "INSERT into camera_log(cam, valid, drct) values (%s,%s,%s)"
    args = (cid, NOW.strftime("%Y-%m-%d %H:%M"), drct)
    cursor.execute(sql, args)

    sql = "DELETE from camera_current WHERE cam = %s"
    args = (cid,)
    cursor.execute(sql, args)

    sql = "INSERT into camera_current(cam, valid, drct) values (%s,%s,%s)"
    args = (cid, NOW.strftime("%Y-%m-%d %H:%M"), drct)
    cursor.execute(sql, args)
    cursor.close()
    dbconn.commit()


def get_row(cid):
    """Get the database row for this camera"""
    dbconn = camutils.get_dbconn()
    if dbconn is None:
        return
    cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""SELECT * from webcams where id = %s """, (cid,))
    row = cursor.fetchone()
    return row


def workflow(cid):
    """Make some magic happen

    We have two image goals:
      - A `fullres` image as per database setting
      - A 640x480 image as for consistent saving
    """
    row = get_row(cid)
    gmt = datetime.datetime.utcnow()
    buf, cam, gmt = get_buffer_and_cam(row, cid, gmt)
    try:
        i0 = Image.open(buf)
    except IOError:
        return

    # Get direction cam is looking
    if row["scrape_url"] is None:
        drct = cam.getDirection()
        dirtext = cam.drct2txt(drct)
    else:
        drct = row["pan0"]
        dirtext = camutils.dir2text(row["pan0"])

    (imgwidth, imgheight) = i0.size
    if imgwidth != 640 or imgheight != 480:
        i640 = i0.resize((640, 480), Image.ANTIALIAS)
        fn640 = draw_save(cid, i640, dirtext, row)
        fnfull = draw_save(cid, i0, dirtext, row)
    else:
        fnfull = draw_save(cid, i0, dirtext, row)
        fn640 = fnfull
    cmd = [
        "pqinsert",
        "-i" "-p",
        (
            f"webcam c {gmt:%Y%m%d%H%M} camera/640x480/{cid}.jpg "
            f"camera/{cid}/{cid}_{gmt:%Y%m%d%H%M}.jpg jpg"
        ),
        fn640,
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stderr = proc.stderr.read()
    if stderr != b"":
        log.warning("cmd: %s stderr:%s", " ".join(cmd), stderr.decode("utf-8"))

    cmd = [
        "pqinsert",
        "-i" "-p",
        (
            f"webcam c {gmt:%Y%m%d%H%M} camera/stills/{cid}.jpg "
            f"camera/{cid}/{cid}_{gmt:%Y%m%d%H%M}.jpg jpg"
        ),
        fnfull,
    ]
    proc = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stderr = proc.stderr.read()
    if stderr != b"":
        log.warning("cmd: %s stderr:%s", " ".join(cmd), stderr.decode("utf-8"))
    # Allow a bit of time for LDM to route the product before the database
    # thinks that it is available
    # TODO: use some more advanced caching
    time.sleep(5)
    do_db(cid, drct)


def main(argv):
    """Do Main Things"""
    cid = argv[1]
    workflow(cid)


if __name__ == "__main__":
    main(sys.argv)
