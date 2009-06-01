#!/usr/bin/env python

from secret import *

from pyIEM import cameras
import sys, logging, os
logging.basicConfig(level=logging.DEBUG)

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam

cid = sys.argv[1]
network = cid[:4]

password = vbcam_pass[network]
user = vbcam_user[network]
if vbcam_user.has_key(cid):
    password = vbcam_pass[cid]
    user = vbcam_user[cid]

c = vbcam.vbcam(id, cameras.cams[cid], user, password)

keys = c.settings.keys()
keys.sort()

for k in keys:
    print "[%s] %s" % (k, c.settings[k])

