# 
from pyiem import iemtz
import ephem
import os
import datetime
import pg
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

import psycopg2
import psycopg2.extras
dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (config.get('database', 'host'),
                                              config.get('database', 'user'),
                                              config.get('database', 'name')))
cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor2 = dbconn.cursor()

now = datetime.datetime.now()
now = now.replace(tzinfo=iemtz.Central)

def mydate(d):
    if d is None:
        return datetime.datetime(1989,1,1)
    if d == "":
        return datetime.datetime(1989,1,1)

    gts = datetime.datetime.strptime(str(d), '%Y/%m/%d %H:%M:%S')
    return gts + datetime.timedelta(seconds=now.utcoffset().seconds)

sun = ephem.Sun()

cursor.execute("""SELECT id, x(geom) as lon, y(geom) as lat from webcams WHERE 
    online = 't' and network in ('KELO','KCCI','KCRG','KCWI') """)

for row in cursor:
    ob = ephem.Observer()
    ob.lat = `row['lat']`
    ob.long = `row['lon']`
    ob.date = '%s 10:00' % (datetime.datetime.utcnow().strftime("%Y/%m/%d"), )
    sun.compute(ob)
    #print row['id'], sun.rise_time, sun.set_time
    r2 = mydate( ob.next_rising(sun) )
    s2 = mydate( ob.next_setting(sun) )

    sql = """UPDATE webcam_scheduler SET 
         begints = '%s'::timestamp - '45 minutes'::interval,
         endts = '%s'::timestamp + '45 minutes'::interval WHERE 
         cid = '%s' and filename ~* '_eve' """ % (
         s2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), row['id'])
    cursor2.execute(sql)
    sql = """UPDATE webcam_scheduler SET 
         begints = '%s'::timestamp - '30 minutes'::interval,
         endts = '%s'::timestamp + '45 minutes'::interval WHERE 
         cid = '%s' and filename ~* '_sunrise' """ % (
         r2.strftime("%Y-%m-%d %H:%M"), r2.strftime("%Y-%m-%d %H:%M"), row['id'])
    cursor2.execute(sql)
    sql = """UPDATE webcam_scheduler SET 
         begints = '%s'::timestamp - '30 minutes'::interval,
         endts = '%s'::timestamp + '30 minutes'::interval WHERE 
         cid = '%s' and filename ~* '_day' """ % (
         r2.strftime("%Y-%m-%d %H:%M"), s2.strftime("%Y-%m-%d %H:%M"), row['id'])
    cursor2.execute(sql)
    
cursor2.close()
dbconn.commit()
dbconn.close()
