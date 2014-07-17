"""
Fire off the aquistion of RT webcam images
"""
import common
cursor = common.get_dbconn().cursor()

import datetime
import sys
import subprocess

now = datetime.datetime.now()

# Figure out how frequently we are to update
cursor.execute("""SELECT propvalue from properties 
    WHERE propname = 'webcam.interval'""")
row = cursor.fetchone()
if row[0] == "300" and now.minute % 5 != 0:
    sys.exit(0)

cursor.execute("""SELECT id from webcams WHERE 
    online = 't' and network in ('KELO','KCCI','KCRG','ISUC', 'KCWI') """)

for row in cursor:
    subprocess.call("python getStill4web.py %s &" % (row[0],), shell=True)
