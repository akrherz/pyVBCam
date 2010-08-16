
from pyIEM import cameras
import os, mx.DateTime
import secret
import pg, sys
mesosite = pg.connect('mesosite', host=secret.DBHOST)

now = mx.DateTime.now()

# Figure out how frequently we are to update
rs = mesosite.query("SELECT * from properties WHERE propname = 'webcam.interval'").dictresult()
if rs[0]['propvalue'] == "300" and now.minute % 5 != 0:
  sys.exit(0)

for cid in cameras.cams.keys():
  if not cameras.cams[cid]['online']:
    continue

  if cid == "KCRG-014" and (now.hour > 17 or now.hour < 8):
    continue

  os.system("/mesonet/python/bin/python getStill4web.py %s &" % (cid,) )
