'''
Simple utility to print out the camera settings 
'''
import common
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

cid = sys.argv[1]
cam = common.get_vbcam(cid)
keys = cam.settings.keys()
keys.sort()

for k in keys:
    print "[%s] %s" % (k, cam.settings[k])

