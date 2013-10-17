'''
Simple utility to print out the camera settings 
'''

import secret
import sys
import logging
import os
import pg
logging.basicConfig(level=logging.DEBUG)

os.chdir(secret.BASE)
sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam

cid = sys.argv[1]
db = pg.connect('mesosite', host=secret.DBHOST, user='nobody')
rs = db.query("""SELECT * from webcams where id = '%s' """ % (cid,)).dictresult()
row = rs[0]
network = row['network']
password = secret.vbcam_pass[network]
user = secret.vbcam_user[network]
if secret.vbcam_user.has_key(cid):
    password = secret.vbcam_pass[cid]
    user = secret.vbcam_user[cid]
if row['is_vapix']:
    cam = vbcam.VAPIX(cid, row, user, password)
else:
    cam = vbcam.vbcam(cid, row, user, password, logLevel=logging.INFO)

keys = cam.settings.keys()
keys.sort()

for k in keys:
    print "[%s] %s" % (k, cam.settings[k])

