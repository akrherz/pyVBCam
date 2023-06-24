"""
Download the frames archived to produce a longterm lapse
"""
from __future__ import print_function

import datetime

import requests


def main():
    """Go!"""
    sts = datetime.datetime(2016, 3, 14, 13)  # Run 13z to 0z
    ets = datetime.datetime(2017, 8, 23)
    interval = datetime.timedelta(minutes=30)

    i = 0
    now = sts
    while now < ets:
        uri = now.strftime(
            (
                "http://mesonet.agron.iastate.edu/archive/"
                "data/%Y/%m/%d/camera/ISUC-002/"
                "ISUC-002_%Y%m%d%H%M.jpg"
            )
        )
        req = requests.get(uri)
        if req.status_code == 200:
            fp = open("/mesonet/tmp/frames/%05d.jpg" % (i,), "w")
            fp.write(req.content)
            fp.close()
            i += 1
        else:
            print("%s -> %s" % (uri, req.status_code))
        if now.hour < 13:
            now += datetime.timedelta(hours=13)
        else:
            now += interval


if __name__ == "__main__":
    main()
