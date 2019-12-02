""" Track either the sun or the moon with a webcam """
import sys
import os
import math
import time
import datetime
import logging
from io import BytesIO

import ephem
from PIL import Image, ImageDraw, ImageFont
from pyvbcam import vbcam


def main(argv):
    """Go Main Go"""
    mydirs = [
        0,
        23,
        45,
        67,
        90,
        112,
        135,
        157,
        180,
        202,
        225,
        247,
        270,
        292,
        315,
        337,
    ]

    fontsize = 22
    font = ImageFont.truetype("../lib/LTe50874.ttf", fontsize)

    cid = argv[1]
    body = argv[2]
    delay = float(argv[3])

    os.chdir("../tmp")
    mydir = ("tracker.%s.%s") % (
        cid,
        datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
    )
    os.makedirs(mydir)
    os.chdir(mydir)
    logging.basicConfig(
        filename="%s.log" % (cid,), filemode="w", level=logging.DEBUG
    )

    if body.lower() == "sun":
        body = ephem.Sun()
        logging.debug("Tracking the sun!")
    else:
        body = ephem.Moon()
        logging.debug("Tracking the moon!")

    cam = vbcam.get_vbcam(cid)

    here = ephem.Observer()
    here.long, here.lat = str(cam.lon), str(cam.lat)

    cam.zoom(30.0)
    cam.getSettings()
    # print cam.settings
    cam.tilt(0)

    stepi = 0
    while True:
        gmt = datetime.datetime.utcnow()
        here.date = gmt.strftime("%Y/%m/%d %H:%M:%S")
        body.compute(here)
        azimuth = float(body.az) * 360.0 / (2 * math.pi)
        alt = float(body.alt) * 360.0 / (2 * math.pi)
        logging.debug("%s AZ: %.4f AL: %.4f", gmt, azimuth, alt)
        if alt < -5:
            time.sleep(delay)
            continue

        cam.panDrct(azimuth)
        # cam.tilt(float(alt) + 2.0)
        # cam.tilt(float(alt))
        drct = cam.getDirection()

        # Create buffer
        buf = BytesIO()
        buf.write(cam.getStillImage())
        buf.seek(0)
        i0 = Image.open(buf)

        draw = ImageDraw.Draw(i0)

        # Drct and Time
        now = datetime.datetime.now()
        s = "%s   %s" % (cam.drct2txt(drct), now.strftime("%-I:%M %p"))
        (w, h) = font.getsize(s)
        draw.rectangle([75, 370, 205, 370 + fontsize], fill="#000000")
        draw.text((200 - w, 370), s, font=font)

        # Center Dot
        draw.rectangle([318, 238, 322, 242], fill="#000000")

        # Tracking details of cam
        # str2 = "%s %s" % (body.az, body.alt)
        # (w, h) = font.getsize(str2)
        # draw.rectangle( [320,250,550,250+h], fill="#000000" )
        # draw.text((550-w,250), str2, font=font)

        # Draw grid lines on the image
        zoom = cam.getZoom()
        leftside = drct - (zoom / 2.0)
        rightside = drct + (zoom / 2.0)
        dx = zoom / 640.0
        for d in mydirs:
            if leftside > d or d > rightside:
                continue

            x = (d - leftside) / dx
            print(
                ("stepi=%s, d=%s, x=%s, left=%s, zoom=%s")
                % (stepi, d, x, leftside, zoom)
            )
            if x < 10 or x > 630:
                continue
            draw.rectangle([x - 2, 230, x + 3, 260], fill="#ffffff")
            draw.rectangle([x - 1, 231, x + 2, 259], fill="#000000")
            ms = cam.drct2txt(d)
            (w, h) = font.getsize(ms)
            draw.rectangle(
                [x - (w / 2) - 1, 260, x + (w / 2) + 1, 260 + fontsize],
                fill="#000000",
            )
            draw.text((x - (w / 2), 260), ms, font=font)

        del draw

        i0.save("%05i.jpg" % (stepi,))
        del i0
        del buf
        # os.system("xv 00000.jpg")
        time.sleep(delay)

        stepi += 1


if __name__ == "__main__":
    main(sys.argv)
