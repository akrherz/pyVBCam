"""
  Drives the production of auto timed webcam lapses
"""
import common

import datetime
import time
import psycopg2.extras
import random
import logging

import sys
import os
import subprocess

sys.path.insert(0, '../vbcam/')
import lapse

dbconn = common.get_dbconn()
cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)


def check_resume(job):
    """ Perhaps we are resuming an old job or re-running post processing? """
    if os.path.isfile("do_auto_lapse.pid"):
        subprocess.call("kill -9 `cat do_auto_lapse.pid`", shell=True)
    if os.path.isfile("%s.log" % (job.site, )):
        os.rename("%s.log" % (job.site, ), "%s.log-OLD" % (job.site, ))

    # Figure out where we left off
    for i in range(job.frames):
        if not os.path.isfile("%05d.jpg" % (i,)):
            break
    job.i = i

    o = open('do_auto_lapse.pid', 'w')
    o.write("%s" % (os.getpid(),))
    o.close()


def setup_job(job):
    """
    Setup our lapse job
    """
    job.init_delay = int(sys.argv[1])
    job.site = sys.argv[2]
    job.network = job.site[:4]
    job.secs = int(float(sys.argv[3]))
    job.filename = sys.argv[4]
    job.movie_duration = int(float(sys.argv[5]))
    job.frames = job.movie_duration * 30

    outdir = "../tmp/autoframes.%s" % (job.filename, )
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    os.chdir(outdir)
    check_resume(job)
    logging.basicConfig(filename="%s.log" % (job.site, ), filemode='w',
                        format='%(levelname)s: %(asctime)-15s %(message)s',
                        level=logging.DEBUG)
    logging.info("We are off and running!")


def bootstrap(job):
    """
    Get us off and running!
    """
    cursor.execute("""SELECT * from webcams where id = %s""", (job.site,))
    row = cursor.fetchone()
    if row['scrape_url'] is None:
        job.camera = common.get_vbcam(row["id"])

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

    # compute
    sts = datetime.datetime.now()
    job.ets = sts + datetime.timedelta(seconds=job.secs)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print(("USAGE: python do_auto_lapse.py init_delay_sec camid "
               "realtime_secs filename movie_secs"))
        sys.exit()
    JOB = lapse.Lapse()
    setup_job(JOB)
    bootstrap(JOB)
    JOB.create_lapse()
    JOB.postprocess()
    if os.path.isfile("do_auto_lapse.pid"):
        os.unlink("do_auto_lapse.pid")
    logging.info("Done!")
