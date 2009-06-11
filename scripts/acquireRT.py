#!/usr/bin/env python

from pyIEM import cameras
import os, mx.DateTime

now = mx.DateTime.now()

for cid in cameras.cams.keys():
  if not cameras.cams[cid]['online']:
    continue

  if cid == "KCRG-014" and (now.hour > 20 or now.hour < 6):
    continue

  os.system("./getStill4web.py %s &" % (cid,) )
