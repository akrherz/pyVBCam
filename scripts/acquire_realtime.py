"""
Fire off the aquistion of RT webcam images
"""

import datetime
import subprocess
import sys

from pyiem.database import get_sqlalchemy_conn, sql_helper
from pyiem.util import logger
from sqlalchemy.engine import Connection

LOG = logger()


def workflow(conn: Connection):
    """Do things we need to do."""
    now = datetime.datetime.now()

    # Figure out how frequently we are to update
    res = conn.execute(
        sql_helper("""
        SELECT propvalue from properties WHERE propname = 'webcam.interval'
    """)
    )
    row = res.mappings().fetchone()
    # assumption is either 60 or 300 is set
    if row["propvalue"] == "300" and now.minute % 5 != 0:
        LOG.info("Not the right time to update webcams, exiting")
        sys.exit(0)

    res = conn.execute(
        sql_helper("""
        SELECT id from webcams WHERE
        online = 't'
        and network in ('KCCI','KCRG','ISUC', 'MCFC')
    """)
    )

    for row in res.mappings():
        # async
        LOG.info("Firing off webcam %s", row["id"])
        subprocess.Popen(
            ["timeout", "55", "python", "get_still_image.py", row["id"]],
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )


def main():
    """Run Main"""
    with get_sqlalchemy_conn("mesosite", rw=False) as conn:
        workflow(conn)


if __name__ == "__main__":
    main()
