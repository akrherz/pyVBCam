"""
Fire off the aquistion of RT webcam images
"""

import datetime
import subprocess
import sys

from pyiem.database import get_dbconnc


def main():
    """Run Main"""
    now = datetime.datetime.now()
    pgconn, cursor = get_dbconnc("mesosite")
    # Figure out how frequently we are to update
    cursor.execute(
        """
        SELECT propvalue from properties WHERE propname = 'webcam.interval'
    """
    )
    row = cursor.fetchone()
    # assumption is either 60 or 300 is set
    if row["propvalue"] == "300" and now.minute % 5 != 0:
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
            ["timeout", "55", "python", "get_still_image.py", row["id"]],
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )


if __name__ == "__main__":
    main()
