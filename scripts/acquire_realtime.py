"""
Fire off the aquistion of RT webcam images
"""
import datetime
import sys
import subprocess

import pyvbcam.utils as camutils


def main():
    """Run Main"""
    now = datetime.datetime.now()
    pgconn = camutils.get_dbconn()
    if pgconn is None:
        return
    cursor = pgconn.cursor()

    # Figure out how frequently we are to update
    cursor.execute(
        """
        SELECT propvalue from properties WHERE propname = 'webcam.interval'
    """
    )
    row = cursor.fetchone()
    # assumption is either 60 or 300 is set
    if row[0] == "300" and now.minute % 5 != 0:
        sys.exit(0)

    cursor.execute(
        """
        SELECT id from webcams WHERE
        online = 't'
        and network in ('KELO','KCCI','KCRG','ISUC', 'MCFC')
    """
    )

    for row in cursor:
        # async
        subprocess.Popen(
            ("timeout 55 python get_still_image.py %s") % (row[0],),
            shell=True,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )


if __name__ == "__main__":
    main()
