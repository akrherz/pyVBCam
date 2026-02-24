"""Simple utility to print out the camera settings"""

import logging
import sys

from pyvbcam import vbcam

logging.basicConfig(level=logging.DEBUG)


def main(argv):
    """Run for this given argument"""
    cid = argv[1]
    cam = vbcam.get_vbcam(cid)
    keys = list(cam.settings.keys())
    keys.sort()

    for k in keys:
        print("[%s] %s" % (k, cam.settings[k]))


if __name__ == "__main__":
    main(sys.argv)
