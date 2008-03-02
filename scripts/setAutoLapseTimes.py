#!/usr/bin/env python
# 
from secret import *

import ephem, mx.DateTime, os
from pyIEM import cameras
import pg
mydb = pg.connect('mesosite', host=DBHOST)

def mydate(d):
  if (d is None): return mx.DateTime.DateTime(1989,1,1)
  if (d == ""): return mx.DateTime.DateTime(1989,1,1)

  gts = mx.DateTime.strptime(str(d), '%Y/%m/%d %H:%M:%S')
  #q = mx.DateTime.gmt()
  #gts += mx.DateTime.RelativeDateTime(year= q.year, month=q.month, day=q.day)
  #print q.day, gts.day
  return gts.localtime()

sun = ephem.Sun()
for id in cameras.cams.keys():
  ob = ephem.Observer()
  ob.lat = `cameras.cams[id]['lat']`
  ob.long = `cameras.cams[id]['lon']`
  ob.date = '%s 10:00' % (mx.DateTime.gmt().strftime("%Y/%m/%d"), )
  sun.compute(ob)
  #print id, sun.rise_time, sun.set_time
  r2 = mydate(sun.rise_time)
  s2 = mydate(sun.set_time)

  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '70 minutes'::interval,\
         endts = '%s'::timestamp + '30 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_eve' " % \
         (s2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), id)
  mydb.query(sql)
  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '30 minutes'::interval,\
         endts = '%s'::timestamp + '70 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_sunrise' " % \
         (r2.strftime("%Y-%m-%d %H:%M"), r2.strftime("%Y-%m-%d %H:%M"), id)
  mydb.query(sql)
  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '30 minutes'::interval,\
         endts = '%s'::timestamp + '30 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_day' " % \
         (r2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), id)
  mydb.query(sql)
