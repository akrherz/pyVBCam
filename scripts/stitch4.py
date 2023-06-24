"""Create a stiched and synced 4-panel, after the fact"""
from __future__ import print_function

import datetime
import glob
import os
import stat

import pandas as pd
from PIL import Image


def main():
    """Go!"""
    # In UTC
    sts = datetime.datetime(2020, 6, 4, 0, 31)
    ets = datetime.datetime(2020, 6, 4, 1, 42)
    didx = pd.date_range(start=sts, end=ets, freq="6S")
    frames = len(didx)

    dirs = [
        "longterm.KCRG-005.20200603183610",
        "longterm.KCRG-006.20200603183610",
        "longterm.KCRG-008.20200603183610",
        "longterm.KCRG-032.20200603183610",
    ]

    dfs = []

    os.chdir("../tmp")
    for mydir in dirs:
        os.chdir(mydir)
        res = []
        files = glob.glob("*.jpg")
        files.sort()
        for fn in files:
            ticks = os.stat(fn)[stat.ST_MTIME]
            valid = datetime.datetime(1970, 1, 1) + datetime.timedelta(
                seconds=ticks
            )
            res.append(dict(fn=fn, valid=valid))
        df = pd.DataFrame(res)
        df.set_index("valid", inplace=True)
        df = df[(df.index >= sts) & (df.index < ets)]
        dfs.append(df.reindex(didx, method="nearest"))
        os.chdir("..")

    if not os.path.isdir("stitch4"):
        os.mkdir("stitch4")
    os.chdir("stitch4")
    for i in range(frames):
        out = Image.new("RGB", (1280, 720))
        fn1 = "../%s/%s" % (dirs[0], dfs[0].iat[i, 0])
        i0 = Image.open(fn1).resize((640, 360))
        out.paste(i0, (0, 0))
        del i0
        fn = "../%s/%s" % (dirs[1], dfs[1].iat[i, 0])
        i0 = Image.open(fn).resize((640, 360))
        out.paste(i0, (640, 0))
        del i0
        fn = "../%s/%s" % (dirs[2], dfs[2].iat[i, 0])
        i0 = Image.open(fn).resize((640, 360))
        out.paste(i0, (0, 360))
        del i0
        fn = "../%s/%s" % (dirs[3], dfs[3].iat[i, 0])
        i0 = Image.open(fn).resize((640, 360))
        out.paste(i0, (640, 360))
        del i0
        out.save("%05i.jpg" % (i,))
        del out


if __name__ == "__main__":
    main()
