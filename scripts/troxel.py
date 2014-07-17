"""
Create frames for our big troxel webcam lapse
"""
import urllib2
import datetime

sts = datetime.datetime(2011,10,30)
ets = datetime.datetime(2013,7,19)
interval = datetime.timedelta(days=7)

i = 0
now = sts
while now < ets:
    for hr in range(16,22):
        for mi in range(0,15,5):
            now = now.replace(hour=hr,minute=mi)
            uri = now.strftime("http://mesonet.agron.iastate.edu/archive/data/%Y/%m/%d/camera/ISUC-001/ISUC-001_%Y%m%d%H%M.jpg")
            try:
                data = urllib2.urlopen(uri).read()
                o = open("../tmp/troxel/%05d.jpg" % (i,), 'w')
                o.write( data )
                o.close()
                i += 1
            except Exception, exp:
                print 'Error', exp
                continue
    uri = now
    
    now += interval