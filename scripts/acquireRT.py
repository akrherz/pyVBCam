"""
Fire off the aquistion of RT webcam images
"""
import common
import datetime
import sys
import subprocess


def main():
    """Run Main"""
    now = datetime.datetime.now()
    try:
        cursor = common.get_dbconn().cursor()
    except:
        # This is a NOOP at the moment, alerting will come from other
        # places when the webcams are stale
        return

    # Figure out how frequently we are to update
    cursor.execute("""
        SELECT propvalue from properties WHERE propname = 'webcam.interval'
        """)
    row = cursor.fetchone()
    # assumption is either 60 or 300 is set
    if row[0] == "300" and now.minute % 5 != 0:
        sys.exit(0)

    cursor.execute("""
        SELECT id from webcams WHERE
        online = 't' and network in ('KELO','KCCI','KCRG','ISUC', 'KCWI')
    """)

    for row in cursor:
        # async
        subprocess.call("python getStill4web.py %s &" % (row[0],), shell=True)

if __name__ == '__main__':
    main()
