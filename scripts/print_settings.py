"""Simple utility to print out the camera settings"""
from __future__ import print_function
import sys
import logging
import common

logging.basicConfig(level=logging.DEBUG)


def main(argv):
    """Run for this given argument"""
    cid = argv[1]
    cam = common.get_vbcam(cid)
    keys = cam.settings.keys()
    keys.sort()

    for k in keys:
        print("[%s] %s" % (k, cam.settings[k]))


if __name__ == '__main__':
    main(sys.argv)
