""" Drive the generation of a long time lapse """
import common

import time
import logging
import StringIO
import mx.DateTime
from PIL import Image, ImageDraw, ImageFont
import sys
import os

fontsize = 18
font = ImageFont.truetype('../lib/veramono.ttf', fontsize)

os.chdir("../tmp/")

site = sys.argv[1]

mydir = "longterm.%s.%s" % (site, mx.DateTime.now().strftime("%Y%m%d%H%M%S"))
os.makedirs(mydir)
os.chdir(mydir)

logging.basicConfig(filename="%s.log" % (site,), filemode='w',
                    level=logging.INFO)
logger = logging.getLogger()

c = common.get_vbcam(site)
logger.info("Camera Settings: %s" % (c.settings, ))


def do(i):
    logging.debug("i = %s" % (i,))

    # Set up buffer for image to go to
    buf = StringIO.StringIO()

    drct = c.getDirection()
    buf.write(c.getOneShot())
    buf.seek(0)
    i0 = Image.open(buf)

    now = mx.DateTime.now()
    s = "%3s %8s" % (c.drct2txt(drct), now.strftime("%-I:%M %p"))
    (w, h) = font.getsize(s)

    draw = ImageDraw.Draw(i0)
    draw.rectangle([205 - w - 10, 370, 205, 370 + h], fill="#000000")
    draw.text((200 - w, 370), s, font=font)
    del draw

    i0.save('%05i.jpg' % (i, ))
    del i0
    del buf
    i += 1

i = 0
errors = 0
while i < 100000:
    time.sleep(int(sys.argv[2]))
    if errors > 100:
        logger.info("Too many errors, abort!")
        break
    try:
        do(i)
    except Exception as exp:
        logger.exception(exp)
        errors += 1
    finally:
        i += 1
