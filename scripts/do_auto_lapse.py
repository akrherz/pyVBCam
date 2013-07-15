"""
  Drives the production of auto timed webcam lapses
"""
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

import datetime
import time
import psycopg2
import random
import logging
from psycopg2.extras import DictCursor
dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (config.get('database', 'host'),
                                              config.get('database', 'user'),
                                              config.get('database', 'name')))
cursor = dbconn.cursor(cursor_factory=DictCursor)

import sys
import os

sys.path.insert(0, '../vbcam/')
import vbcam, lapse

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

    outdir = "../tmp/autoframes.%s_%s" % (job.filename, 
                                   datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    os.makedirs(outdir)
    os.chdir(outdir)

    logging.basicConfig(filename="%s.log" % (job.site, ), filemode='w',
                    format='%(levelname)s: %(asctime)-15s %(message)s', 
                    level=logging.DEBUG )
    logging.info("We are off and running!")

def bootstrap(job):
    """
    Get us off and running!
    """
    cursor.execute("""SELECT * from webcams where id = %s""", (job.site,) )
    row = cursor.fetchone()
    if row['scrape_url'] is None:
        network = row['network']
        password = config.get(network, 'password')
        user = config.get(network, 'user')
        if config.has_section(job.site):
            password = config.get(job.site, 'password')
            user = config.get(job.site, 'user')
        if row['is_vapix']:
            job.camera = vbcam.VAPIX(job.site, row, user, password)
        else:
            job.camera = vbcam.vbcam(job.site, row, user, password)

    
        if job.camera.settings == {}:
            logging.info("Failed to reach camera, aborting...")
            sys.exit(0)
    else:
        job.camera = lapse.scrape(job.site, row)

    cursor.close()
    dbconn.close()

    # Initially sleep until it is go time!
    logging.debug("Initial sleep of: %s", job.init_delay)
    time.sleep(job.init_delay + random.random() )

    # compute
    sts = datetime.datetime.now()
    job.ets = sts + datetime.timedelta(seconds = job.secs)

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print 'USAGE: python do_auto_lapse.py init_delay_sec camid realtime_secs filename movie_secs'
        sys.exit()
    JOB = lapse.Lapse()
    setup_job(JOB)
    bootstrap(JOB)
    JOB.create_lapse()
    JOB.postprocess()
    logging.info("Done!")
