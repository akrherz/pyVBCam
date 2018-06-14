""" Create a panoramic image for a given site """
import sys
import time
import os
import logging

from PIL import Image, ImageDraw
from pywebcam import vbcam
logging.basicConfig(level=logging.DEBUG)


def main(argv):
    """Go Main Go"""
    os.chdir("../tmp")

    # Which webcam, establish existing lat/lon and pan0
    cid = argv[1]
    camera = vbcam.get_vbcam(cid)
    camera.zoom(40.0)
    camera.tilt(0.0)
    out = Image.new('RGB', (720, 480))

    i = 0
    for ang in range(-160, 180, 40):
        print("Working on Angle: %s" % (ang,))
        camera.pan(ang)
        time.sleep(2)  # Settle down the cam
        o = open("tmp.jpg", 'wb')
        o.write(camera.getStillImage())
        o.close()

        i0 = Image.open("tmp.jpg")
        i02 = i0.resize((144, 240))
        draw = ImageDraw.Draw(i02)
        draw.rectangle([0, 119, 144, 121], fill="#000000")

        row = int(i/5)
        col = i % 5
        out.paste(i02, (144*col, row*240))
        if i == 4:
            i = 5
            row = int(i/5)
            col = i % 5
            out.paste(i02, (124*col, row*240))
        del i0, i02
        i += 1

    out.save("%s_panorama.jpg" % (cid,))
    del out


if __name__ == '__main__':
    main(sys.argv)
