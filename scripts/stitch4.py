"""Create a stiched and synced 4-panel, after the fact"""
import pandas as pd
import datetime
import os
import stat
import glob
from PIL import Image

# In UTC
sts = datetime.datetime(2016, 7, 13, 22, 40)
ets = datetime.datetime(2016, 7, 14, 0, 57)
didx = pd.date_range(start=sts, end=ets, freq='8S')
frames = len(didx)

dirs = ['longterm.KCCI-001.20160713111337',
        'longterm.KCCI-004.20160713111337',
        # 'longterm.KCCI-010.20160713111337',
        'longterm.KCCI-028.20160713111337']

dfs = []

os.chdir("../tmp")
for mydir in dirs:
    os.chdir(mydir)
    res = []
    files = glob.glob("*.jpg")
    files.sort()
    for fn in files:
        ticks = os.stat(fn)[stat.ST_MTIME]
        valid = (datetime.datetime(1970, 1, 1) +
                 datetime.timedelta(seconds=ticks))
        res.append(dict(fn=fn, valid=valid))
    df = pd.DataFrame(res)
    df.set_index('valid', inplace=True)
    df = df[(df.index >= sts) & (df.index < ets)]
    dfs.append(df.reindex(didx, method='nearest'))
    os.chdir("..")

if not os.path.isdir('stitch4'):
    os.mkdir("stitch4")
os.chdir('stitch4')
for i in range(frames):
    out = Image.new('RGB', (1280, 960))
    fn1 = "../%s/%s" % (dirs[0], dfs[0].iat[i, 0])
    i0 = Image.open(fn1)
    out.paste(i0, (0, 0))
    del i0
    fn = "../%s/%s" % (dirs[1], dfs[1].iat[i, 0])
    i0 = Image.open(fn)
    out.paste(i0, (640, 0))
    del i0
    fn = "../%s/%s" % (dirs[2], dfs[2].iat[i, 0])
    i0 = Image.open(fn)
    out.paste(i0, (320, 480))
    del i0
    # fn = "../%s/%s" % (dirs[3], dfs[3].iat[i, 0])
    # i0 = Image.open(fn)
    # out.paste(i0, (640, 480))
    # del i0
    out.save('%05i.jpg' % (i,))
    del out
