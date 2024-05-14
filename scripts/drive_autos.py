"""proctor the exec of daily auto lapse scripts"""

import datetime
import subprocess
import time

import click
from pyiem.database import get_dbconnc
from pyiem.util import logger

LOG = logger()


@click.command()
@click.option("--label", help="Load jobs for a specific label.")
def main(label):
    """Go Main"""
    dbconn, cursor = get_dbconnc("mesosite")

    lookingfor = datetime.datetime.now().strftime("%Y%m%d%H")

    if label is not None:
        cursor.execute(
            """
            SELECT s.*, s.oid from webcam_scheduler s JOIN webcams c
            on (s.cid = c.id) WHERE c.online is TRUE and
            strpos(filename, %s) > 0 and is_daily IS TRUE
        """,
            (label,),
        )

    else:
        cursor.execute(
            """
            SELECT s.*, s.oid from webcam_scheduler s JOIN webcams c
            on (s.cid = c.id) WHERE c.online is TRUE and
            (to_char(begints, 'YYYYMMDDHH24') = %s or
            (to_char(begints, 'HH24') = %s and is_daily IS TRUE))
        """,
            (lookingfor, lookingfor[8:]),
        )
    LOG.info("Found %s database rows", cursor.rowcount)
    for row in cursor:
        sts = row["begints"]
        ets = row["endts"]
        if ets < sts:
            ets += datetime.timedelta(days=1)
        movie_seconds = row["movie_seconds"]
        secs = (ets - sts).seconds
        init_delay = sts.minute * 60
        # is the amphersand necessary?
        cmd = [
            "python",
            "do_auto_lapse.py",
            f"{init_delay}",
            row["cid"],
            f"{secs}",
            row["filename"],
            f"{movie_seconds}",
        ]
        subprocess.call(cmd)
        time.sleep(1)  # Jitter to keep dups

        if not row["is_daily"]:
            cursor.execute(
                "DELETE from webcam_scheduler WHERE oid = %s",
                (row["oid"],),
            )

    cursor.close()
    dbconn.commit()
    dbconn.close()


if __name__ == "__main__":
    main()
