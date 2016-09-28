"""
Download the frames archived to produce a longterm lapse
"""
import requests
import datetime

sts = datetime.datetime(2016, 9, 22)
ets = datetime.datetime(2016, 9, 25)
interval = datetime.timedelta(minutes=5)

i = 0
now = sts
while now < ets:
    uri = now.strftime(("http://mesonet.agron.iastate.edu/archive/"
                        "data/%Y/%m/%d/camera/KCRG-022/"
                        "KCRG-022_%Y%m%d%H%M.jpg"))
    req = requests.get(uri)
    if req.status_code == 200:
        o = open("/mesonet/tmp/frames/%05d.jpg" % (i,), 'w')
        o.write(req.content)
        o.close()
        i += 1
    else:
        print("%s -> %s" % (uri, req.status_code))
    uri = now

    now += interval
