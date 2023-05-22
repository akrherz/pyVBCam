""" Create a 16 panel lapse, after the fact :) """
import datetime
import glob
import os

from PIL import Image

cams = [
    "KCRG-001",
    "KCRG-002",
    "KCRG-003",
    "KCRG-005",
    "KCRG-006",
    "KCRG-007",
    "KCRG-008",
    "KCRG-009",
    "KCRG-010",
    "KCRG-011",
    "KCRG-012",
    "KCRG-016",
    "KCRG-018",
    "KCRG-020",
    "KCRG-022",
    "KCRG-023",
]


def compute_timestamps():
    """Build a dictionary of timestamps"""
    res = {}
    for cam in cams:
        res[cam] = {}
        mydir = "longterm.%s.20140904183833" % (cam,)
        os.chdir(mydir)
        for fn in glob.glob("*.jpg"):
            res[cam]["%s/%s" % (mydir, fn)] = datetime.datetime.fromtimestamp(
                os.path.getmtime(fn)
            )
        os.chdir("..")
    return res


def get_timeline():
    """Get the timeline we want to lapse for"""
    frames = 600
    sts = datetime.datetime(2014, 9, 4, 18, 38)
    ets = datetime.datetime(2014, 9, 4, 19, 50)
    interval = (ets - sts).seconds / float(frames)
    now = sts
    timeline = []
    while now < ets:
        timeline.append(now)
        now += datetime.timedelta(seconds=interval)

    return timeline


def get_delta(t1, t2):
    """Compute difference"""
    d = t1 - t2
    delta = d.days * 86400.0 + d.seconds + d.microseconds / 1000000.0
    return abs(delta)


def get_files(timestamps, valid):
    """Figure out our closest file"""
    res = []
    for cam in cams:
        mindelta = 999999
        minfn = None
        for fn in timestamps[cam]:
            delta = get_delta(timestamps[cam][fn], valid)
            if delta < mindelta:
                mindelta = delta
                minfn = fn
        res.append(minfn)
    return res


def main():
    """Go Main Go"""
    os.chdir("../tmp")
    timestamps = compute_timestamps()
    timeline = get_timeline()
    mydir = "panel16.%s" % (datetime.datetime.now().strftime("%Y%m%d%H%M%S"),)
    os.makedirs(mydir)
    for t, valid in enumerate(timeline):
        frame = Image.new("RGB", (1280, 960))
        files = get_files(timestamps, valid)
        for i, imgfn in enumerate(files):
            row = i / 4
            col = i % 4
            x = col * 320
            y = row * 240
            i0 = Image.open(imgfn)
            i0 = i0.resize((320, 240))
            frame.paste(i0, (x, y))

        frame.save("%s/%05i.jpg" % (mydir, t))


if __name__ == "__main__":
    # Go Main Go
    main()
