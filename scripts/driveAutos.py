#!/usr/bin/env python
# Drive build script!

from secret import *

import mx.DateTime, os, time

import pg
mesosite = pg.connect('mesosite', host=DBHOST)

lookingfor = mx.DateTime.now().strftime("%Y%m%d%H")

sql = "SELECT *, oid from webcam_scheduler WHERE to_char(begints, 'YYYYMMDDHH24') = '%s' or (to_char(begints, 'HH24') = '%s' and is_daily IS TRUE)" % (lookingfor, lookingfor[8:])
rs = mesosite.query(sql).dictresult()

for i in range(len(rs)):
  sts = mx.DateTime.strptime(rs[i]['begints'][:16], "%Y-%m-%d %H:%M")
  ets = mx.DateTime.strptime(rs[i]['endts'][:16], "%Y-%m-%d %H:%M")
  if (ets < sts):
    ets += mx.DateTime.RelativeDateTime(days=1)
  movie_seconds = float(rs[i]['movie_seconds'])
  secs = (ets - sts).seconds
  init_delay = (sts.minute * 60)
  #delay = int(secs / (movie_seconds * 30) - 3)
  #if (delay < 0): delay = 0
  cmd = "./siteAutoDrive.py %s %s %s %s %s &" % (init_delay, rs[i]['cid'], secs, rs[i]['filename'], movie_seconds)
  #print cmd
  os.system(cmd)
  time.sleep(1)  # Jitter to keep dups

  if (rs[i]['is_daily'] == 'f'):
    mesosite.query("DELETE from webcam_scheduler WHERE oid = %s" % (rs[i]['oid'],) )
