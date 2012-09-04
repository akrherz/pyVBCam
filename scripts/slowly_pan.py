"""
Slowly pan the webcam in some direction
"""
import logging
logging.basicConfig(level=logging.DEBUG)
import sys
import secret
import sys
import os
os.chdir(secret.BASE)
sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
cid = sys.argv[1]
network = cid[:4]
degrees = float(sys.argv[2])

import pg
mesosite = pg.connect('mesosite', host=secret.DBHOST, user='nobody')

rs = mesosite.query("""SELECT *, x(geom) as lon, y(geom) as lat from webcams 
    where id = '%s'""" % (cid,)).dictresult()
row = rs[0]
cam = vbcam.vbcam(cid, row, 
                  secret.vbcam_user[network], secret.vbcam_pass[network] )

dir = float(cam.settings['pan_current_value']) / 100.0
print 'In: %.2f pan: %.0f' % (dir, degrees)
cam.pan( dir + degrees ) 
cam.getSettings()
dir = float(cam.settings['pan_current_value']) / 100.0
print 'Out: %.2f' % (dir,)
cam.closeConnection()
