#!/usr/bin/env python

from pyIEM import cameras
import os

for cid in cameras.cams.keys():
  if not cameras.cams[cid]['online']:
    continue

  os.system("./getStill4web.py %s &" % (cid,) )
