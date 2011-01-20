# 
import secret
import ephem, mx.DateTime, os
import pg
mesosite = pg.connect('mesosite', host=secret.DBHOST)

def mydate(d):
  if (d is None): return mx.DateTime.DateTime(1989,1,1)
  if (d == ""): return mx.DateTime.DateTime(1989,1,1)

  gts = mx.DateTime.strptime(str(d), '%Y/%m/%d %H:%M:%S')
  #q = mx.DateTime.gmt()
  #gts += mx.DateTime.RelativeDateTime(year= q.year, month=q.month, day=q.day)
  #print q.day, gts.day
  return gts.localtime()

sun = ephem.Sun()

rs = mesosite.query("""SELECT id, x(geom) as lon, y(geom) as lat from webcams WHERE 
    online = 't' and network in ('KELO','KCCI','KCRG') """).dictresult()

for row in rs:
  ob = ephem.Observer()
  ob.lat = `row['lat']`
  ob.long = `row['lon']`
  ob.date = '%s 10:00' % (mx.DateTime.gmt().strftime("%Y/%m/%d"), )
  sun.compute(ob)
  #print id, sun.rise_time, sun.set_time
  r2 = mydate( ob.next_rising(sun) )
  s2 = mydate( ob.next_setting(sun) )

  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '45 minutes'::interval,\
         endts = '%s'::timestamp + '45 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_eve' " % \
         (s2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), id)
  mesosite.query(sql)
  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '30 minutes'::interval,\
         endts = '%s'::timestamp + '45 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_sunrise' " % \
         (r2.strftime("%Y-%m-%d %H:%M"), r2.strftime("%Y-%m-%d %H:%M"), id)
  mesosite.query(sql)
  sql = "UPDATE webcam_scheduler SET \
         begints = '%s'::timestamp - '30 minutes'::interval,\
         endts = '%s'::timestamp + '30 minutes'::interval WHERE \
         cid = '%s' and filename ~* '_day' " % \
         (r2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), id)
  mesosite.query(sql)
