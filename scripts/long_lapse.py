""" Drive the generation of a long time lapse """
import time
import sys
import os
import logging
from io import BytesIO
import datetime

from PIL import Image, ImageDraw, ImageFont
from pyvbcam.vbcam import get_vbcam


def doimage(cam, i, font):
    """Do the image workflow"""
    logging.debug("i = %s", i)

    # Set up buffer for image to go to
    buf = BytesIO()

    drct = cam.getDirection()
    buf.write(cam.get_one_shot())
    buf.seek(0)
    i0 = Image.open(buf)
    imgheight = i0.size[1]

    now = datetime.datetime.now()
    label = "%3s %8s" % (cam.drct2txt(drct), now.strftime("%-I:%M %p"))
    (width, height) = font.getsize(label)

    draw = ImageDraw.Draw(i0)
    draw.rectangle(
        [205 - width - 10, imgheight - 110, 205, imgheight - 110 + height],
        fill="#000000",
    )
    draw.text((200 - width, imgheight - 110), label, font=font)
    del draw

    i0.save("%05i.jpg" % (i,))
    del i0
    del buf
    i += 1


def main(argv):
    """Do Main"""
    fontsize = 18
    font = ImageFont.truetype("../lib/veramono.ttf", fontsize)

    os.chdir("../tmp/")

    site = argv[1]

    mydir = ("longterm.%s.%s") % (
        site,
        datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    )
    os.makedirs(mydir)
    os.chdir(mydir)

    logging.basicConfig(
        filename="%s.log" % (site,), filemode="w", level=logging.INFO
    )
    logger = logging.getLogger()

    cam = get_vbcam(site)
    logger.info("Camera Settings: %s", cam.settings)

    i = 0
    errors = 0
    while i < 100000:
        time.sleep(int(argv[2]))
        if errors > 100:
            logger.info("Too many errors, abort!")
            break
        try:
            doimage(cam, i, font)
        except Exception as exp:
            logger.exception(exp)
            errors += 1
            continue
        i += 1


if __name__ == "__main__":
    main(sys.argv)
