

import os, mx.DateTime
import secret
import pg, sys
mesosite = pg.connect('mesosite', host=secret.DBHOST)

now = mx.DateTime.now()

# Figure out how frequently we are to update
rs = mesosite.query("SELECT * from properties WHERE propname = 'webcam.interval'").dictresult()
if rs[0]['propvalue'] == "300" and now.minute % 5 != 0:
  sys.exit(0)

rs = mesosite.query("""SELECT id from webcams WHERE 
    online = 't' and network in ('KELO','KCCI','KCRG','ISUC') """).dictresult()

for row in rs:
    os.system("python getStill4web.py %s &" % (row['id'],) )
