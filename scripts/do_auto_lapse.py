"""
Drives the production of auto timed webcam lapses
"""

import datetime
import logging
import os
import random
import subprocess
import sys
import time

import click
import posix_ipc
from pyiem.database import get_dbconnc
from pyiem.util import utc

from pyvbcam import lapse, vbcam

# Limit postprocessing to 4 at a time
SEMAPHORE = posix_ipc.Semaphore(
    "/pyvbcam_postprocess",
    flags=posix_ipc.O_CREAT,
    initial_value=4,
)


def check_resume(job):
    """Perhaps we are resuming an old job or re-running post processing?"""
    if os.path.isfile("do_auto_lapse.pid"):
        subprocess.call("kill -9 `cat do_auto_lapse.pid`", shell=True)
    if os.path.isfile("%s.log" % (job.site,)):
        os.rename("%s.log" % (job.site,), "%s.log-OLD" % (job.site,))

    # Figure out where we left off
    for i in range(job.frames):
        if not os.path.isfile("%05d.jpg" % (i,)):
            break
    job.i = i

    output = open("do_auto_lapse.pid", "w")
    output.write("%s" % (os.getpid(),))
    output.close()


def setup_job(job, cid, sts, ets, label, duration):
    """
    Setup our lapse job
    """
    job.site = cid
    job.ets = ets
    job.network = job.site[:4]
    job.filename = label
    job.movie_duration = duration
    job.frames = job.movie_duration * 30

    # Figure out how much to delay the start
    diff = (sts - utc()).total_seconds()
    job.init_delay = 0 if diff < 0 else int(diff)

    outdir = "../tmp/autoframes.%s" % (job.filename,)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)
    check_resume(job)
    logging.basicConfig(
        filename="%s.log" % (job.site,),
        filemode="w",
        format="%(levelname)s: %(asctime)-15s %(message)s",
        level=logging.DEBUG,
    )
    logging.info("We are off and running!")


def bootstrap(job):
    """
    Get us off and running!
    """
    dbconn, cursor = get_dbconnc("mesosite")
    cursor.execute("SELECT * from webcams where id = %s", (job.site,))
    row = cursor.fetchone()
    if row["scrape_url"] is None:
        job.camera = vbcam.get_vbcam(row["id"])

        if job.camera.settings == {}:
            logging.info("Failed to reach camera, aborting...")
            sys.exit(0)
    else:
        job.camera = lapse.scrape(job.site, row)

    cursor.close()
    dbconn.close()

    # Initially sleep until it is go time!
    logging.debug("Initial sleep of: %s", job.init_delay)
    time.sleep(job.init_delay + random.random())


@click.command()
@click.option("--cid", required=True, help="Camera ID")
@click.option("--sts", required=True, type=click.DateTime(), help="UTC Start")
@click.option("--ets", required=True, type=click.DateTime(), help="UTC End")
@click.option("--label", required=True, help="Generated lapse name.")
@click.option("--duration", required=True, type=int, help="Duration seconds")
def main(cid, sts, ets, label, duration):
    """Do Something"""
    sts = sts.replace(tzinfo=datetime.timezone.utc)
    ets = ets.replace(tzinfo=datetime.timezone.utc)
    job = lapse.Lapse()
    setup_job(job, cid, sts, ets, label, duration)
    bootstrap(job)
    job.create_lapse()
    SEMAPHORE.acquire()
    try:
        job.postprocess()
    finally:
        SEMAPHORE.release()
    if os.path.isfile("do_auto_lapse.pid"):
        os.unlink("do_auto_lapse.pid")
    logging.info("Done!")


if __name__ == "__main__":
    main()
