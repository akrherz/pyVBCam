"""Create a stiched and synced 4-panel, after the fact"""

import datetime
import glob
import os
import stat

import pandas as pd
from PIL import Image
from tqdm import tqdm


def main():
    """Go!"""
    # In UTC
    sts = datetime.datetime(2021, 8, 26, 14, 40)
    ets = datetime.datetime(2021, 8, 26, 14, 57)
    didx = pd.date_range(start=sts, end=ets, freq="3S")
    frames = len(didx)

    dirs = [
        "longterm.ISUC-004.20210826085007",
        "longterm.ISUC-005.20210826085008",
        "longterm.ISUC-006.20210826085008",
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
        df = df.set_index("valid")
        df = df[(df.index >= sts) & (df.index < ets)]
        dfs.append(df.reindex(didx, method="nearest"))
        os.chdir("..")
    if not os.path.isdir("stitch3_isu"):
        os.mkdir("stitch3_isu")
    os.chdir("stitch3_isu")
    progress = tqdm(range(frames))
    for i in progress:
        out = Image.new("RGB", (1920, 1080))
        # Squeeze and resize
        fn1 = "../%s/%s" % (dirs[0], dfs[0].iat[i, 0])
        i0 = Image.open(fn1).resize((640, 640))
        out.paste(i0, (0, 180))
        del i0
        fn = "../%s/%s" % (dirs[1], dfs[1].iat[i, 0])
        i0 = Image.open(fn).resize((640, 640))
        out.paste(i0, (640, 180))
        del i0
        fn = "../%s/%s" % (dirs[2], dfs[2].iat[i, 0])
        i0 = Image.open(fn).resize((640, 640))
        out.paste(i0, (1280, 180))
        del i0
        out.save("%05i.jpg" % (i,))
        del out


if __name__ == "__main__":
    main()
