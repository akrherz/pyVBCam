#!/mesonet/python/bin/python
# Script to set the camera to some location

import secret, sys, os, time
from pyIEM import cameras

os.chdir(secret.BASE)
sys.path = [secret.BASE+"/vbcam"] + sys.path
import vbcam
os.chdir("tmp/")


database = {
 'KELO-001': {'p': 38.68, 't': 5.84, 'z': 41.26},
 'KELO-002': {'p': -56.28, 't': 0.52, 'z': 41.26},
 'KELO-003': {'p': 68.4, 't': -5.73, 'z': 41.26},
 'KELO-004': {'p': 15.51, 't': -3.19, 'z': 22.12},
 'KCCI-016': {'p': 0.08, 't': 0.93, 'z': 25.75},
}


cid = sys.argv[1]
network = cid[:4]
password = secret.vbcam_pass[network]
user = secret.vbcam_user[network]
if secret.vbcam_user.has_key(cid):
    password = secret.vbcam_pass[cid]
    user = secret.vbcam_user[cid]
cam = vbcam.vbcam(cid, cameras.cams[cid], user, password)

cam.pan( database[cid]['p'] )
time.sleep(1)
cam.tilt( database[cid]['t'] )
time.sleep(1)
cam.zoom( database[cid]['z'] )
time.sleep(1)

cam.pan( database[cid]['p'] )
time.sleep(1)
cam.tilt( database[cid]['t'] )
time.sleep(1)
cam.zoom( database[cid]['z'] )
time.sleep(1)

cam.closeConnection()
