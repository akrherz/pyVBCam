""" Drive the generation of a long time lapse """
import datetime
import logging
import os
import sys
import time
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from pyvbcam.utils import DATADIR
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
    draw = ImageDraw.Draw(i0)

    now = datetime.datetime.now()
    label = "%3s %8s" % (cam.drct2txt(drct), now.strftime("%-I:%M %p"))
    labelpt = (125, imgheight - 90)
    bbox = draw.textbbox(labelpt, label, font=font, anchor="mm")
    height = bbox[3] - bbox[1]
    width = bbox[2] - bbox[0]

    draw.rectangle(
        [
            labelpt[0] - width / 2.0 - 5,
            labelpt[1] - height / 2.0 - 5,
            labelpt[0] + width / 2.0 + 5,
            labelpt[1] + height / 2.0 + 5,
        ],
        fill="#000000",
    )
    draw.text(labelpt, label, font=font, anchor="mm")
    del draw

    i0.save("%05i.jpg" % (i,))
    del i0
    del buf
    i += 1


def main(argv):
    """Do Main"""
    fontsize = 18
    font = ImageFont.truetype(DATADIR + "/veramono.ttf", fontsize)

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
    # hack around flakey webcam issue for now
    errors_limit = 100 if site not in ["KCRG-031", "KCRG-032"] else 1000
    while i < 100000:
        time.sleep(int(argv[2]))
        if errors > errors_limit:
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
