""" Sync four webcams in time generating a timelapse """
import common

from PIL import Image, ImageDraw, ImageFont
import mx.DateTime
import sys
import time
import os
import logging

os.chdir("../tmp")

cams = []
for camid in sys.argv[1:5]:
    print 'Adding %s webcam' % (camid,)
    cams.append(common.get_vbcam(camid))

x = [0, 320, 0, 320]
y = [0, 0, 240, 240]

fontsize = 22
font = ImageFont.truetype('../lib/veramono.ttf', fontsize)

mydir = "iemsync.%s" % (mx.DateTime.now().strftime("%Y%m%d%H%M%S"),)
os.makedirs(mydir)
os.chdir(mydir)

logging.basicConfig(filename="iemsync.log", filemode='w')


for i in range(100000):
    # Output
    out = Image.new('RGB', (640, 480))

    for j in range(4):
        # print cams[j].getDirection()
        o = open("%s_%s.jpg" % (i, j), 'w')
        cnt = 0
        while (cnt < 10):
            try:
                o.write(cams[j].get_one_shot())
                cnt = 100
            except:
                cnt += 1
        o.close()

        i0 = Image.open("%s_%s.jpg" % (i, j))

        i02 = i0.resize((320, 240))
        out.paste(i02, (x[j], y[j]))
        del i0
        del i02
        os.remove("%s_%s.jpg" % (i, j))

    draw = ImageDraw.Draw(out)
    draw.rectangle([280, 220, 360, 260], fill="#000000")
    now = mx.DateTime.now()
    s = now.strftime("%I:%M")
    draw.text((290, 229), s, font=font)
    del draw

    out.save('%05i.jpg' % (i,))
    del out
    time.sleep(int(sys.argv[5]))
