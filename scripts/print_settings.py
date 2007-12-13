#!/usr/bin/env python

from secret import *

from pyIEM import cameras
import sys, logging, os
logging.basicConfig(level=logging.DEBUG)

os.chdir(BASE)
sys.path = [BASE+"/vbcam"] + sys.path
import vbcam

id = sys.argv[1]
network = id[:4]

c = vbcam.vbcam(id, cameras.cams[id], vbcam_user[network], vbcam_pass[network])

keys = c.settings.keys()
keys.sort()

for k in keys:
    print "[%s] %s" % (k, c.settings[k])

