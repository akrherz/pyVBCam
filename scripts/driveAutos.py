"""
 Drive build script!
"""
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

import datetime
import time
import subprocess
import psycopg2
import psycopg2.extras
dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (config.get('database', 'host'),
                                              config.get('database', 'user'),
                                              config.get('database', 'name')))
cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

lookingfor = datetime.datetime.now().strftime("%Y%m%d%H")

sql = """SELECT *, oid from webcam_scheduler WHERE 
    to_char(begints, 'YYYYMMDDHH24') = '%s' or (to_char(begints, 'HH24') = '%s' 
    and is_daily IS TRUE)""" % (lookingfor, lookingfor[8:])
cursor.execute(sql)

for row in cursor:
    sts = row['begints']
    ets = row['endts']
    if ets < sts:
        ets += datetime.timedelta(days=1)
    movie_seconds = row['movie_seconds']
    secs = (ets - sts).seconds
    init_delay = sts.minute * 60
    cmd = "python do_auto_lapse.py %s %s %s %s %s &" % (init_delay, 
                    row['cid'], secs, row['filename'], movie_seconds)
    subprocess.call(cmd, shell=True)
    time.sleep(1)  # Jitter to keep dups

    if not row['is_daily']:
        cursor.execute("DELETE from webcam_scheduler WHERE oid = %s" % (row['oid'],) )

cursor.close()
dbconn.commit()
dbconn.close()
