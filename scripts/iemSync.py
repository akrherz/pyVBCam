#!/usr/bin/env python

from secret import *

from PIL import Image, ImageDraw, ImageFont
from pyIEM import cameras
import mx.DateTime, sys, time, os, logging

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")

cams = []
for id in sys.argv[1:5]:
    network = id[:4]
    print network, id
    cams.append( vbcam.vbcam(id, cameras.cams[id], vbcam_user[network], vbcam_pass[network]) )

x = [0,320,0,320]
y = [0,0,240,240]

font = ImageFont.truetype(BASE+'lib/veramono.ttf', 22)

dir = "iemsync.%s" % (mx.DateTime.now().strftime("%Y%m%d%H%M%S"),)
os.makedirs(dir)
os.chdir(dir)

logging.basicConfig(filename="iemsync.log",filemode='w' )


for i in range(100000):
    # Output
    out = Image.new('RGB', (640,480) )

    for j in range(4):
        #print cams[j].getDirection()
        o = open("%s_%s.jpg" % (i,j), 'w')
        cnt = 0
        while (cnt < 10):
            try:
                o.write( cams[j].getOneShot() )
                cnt = 100
            except:
                cnt += 1
        o.close()

        i0 = Image.open("%s_%s.jpg" % (i,j) )

        i02 = i0.resize( (320,240) )
        out.paste(i02, (x[j],y[j]))
        del i0
        del i02
        os.remove("%s_%s.jpg" % (i,j) )

    draw = ImageDraw.Draw(out)
    draw.rectangle( [280,220,360,260], fill="#000000" )
    now = mx.DateTime.now()
    str = now.strftime("%I:%M")
    draw.text((290,229), str, font=font)
    del draw 

    out.save('%05i.jpg' % (i,))
    del out
    time.sleep(int(sys.argv[5]))
