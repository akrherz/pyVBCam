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
        sts = row["begints"].astimezone(datetime.timezone.utc)
        ets = row["endts"].astimezone(datetime.timezone.utc)
        # A quirk of pyephem at one time, unsure if still valid.
        if ets < sts:
            ets += datetime.timedelta(days=1)
        cmd = [
            "python",
            "do_auto_lapse.py",
            "--cid",
            row["cid"],
            "--sts",
            f"{sts:%Y-%m-%dT%H:%M:%S}",
            "--ets",
            f"{ets:%Y-%m-%dT%H:%M:%S}",
            "--label",
            row["filename"],
            "--duration",
            f"{row['movie_seconds']}",
        ]
        subprocess.Popen(cmd)  # needed to background
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
