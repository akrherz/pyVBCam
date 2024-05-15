"""Update the database to set proper times."""

import datetime
from zoneinfo import ZoneInfo

import ephem
from pyiem.database import get_dbconnc
from pyiem.util import utc

NOW = datetime.datetime.now().replace(tzinfo=ZoneInfo("America/Chicago"))


def mydate(tstamp):
    """Convert this string to a proper timestamp"""
    gts = datetime.datetime.strptime(str(tstamp), "%Y/%m/%d %H:%M:%S")
    return gts.replace(tzinfo=datetime.timezone.utc)


def main():
    """Do things please!"""
    dbconn, cursor = get_dbconnc("mesosite")
    cursor2 = dbconn.cursor()

    sun = ephem.Sun()

    cursor.execute(
        """
        SELECT id, ST_x(geom) as lon, ST_y(geom) as lat from webcams WHERE
        online = 't' and network in ('KCCI','KCRG','ISUC', 'MCFC')
        """
    )

    for row in cursor:
        ob = ephem.Observer()
        ob.lat = str(row["lat"])
        ob.long = str(row["lon"])
        ob.date = f"{utc():%Y/%m/%d} 08:00"  # UTC
        sun.compute(ob)
        r2 = mydate(ob.next_rising(sun))
        s2 = mydate(ob.next_setting(sun))

        # set morning and afternoon
        cursor2.execute(
            """
            update webcam_scheduler set begints = %s, endts = %s
            where cid = %s and strpos(filename, '_morning') > 0
            and is_daily
            """,
            (
                NOW.replace(hour=8, minute=0, second=0, microsecond=0),
                NOW.replace(hour=11, minute=0, second=0, microsecond=0),
                row["id"],
            ),
        )
        cursor2.execute(
            """
            update webcam_scheduler set begints = %s, endts = %s
            where cid = %s and strpos(filename, '_afternoon') > 0
            and is_daily
            """,
            (
                NOW.replace(hour=13, minute=0, second=0, microsecond=0),
                NOW.replace(hour=16, minute=0, second=0, microsecond=0),
                row["id"],
            ),
        )

        cursor2.execute(
            """
            UPDATE webcam_scheduler SET begints = %s, endts = %s WHERE
            cid = %s and filename ~* '_eve'
        """,
            (
                s2 - datetime.timedelta(minutes=45),
                s2 + datetime.timedelta(minutes=45),
                row["id"],
            ),
        )
        cursor2.execute(
            """
            UPDATE webcam_scheduler SET begints = %s, endts = %s WHERE
            cid = %s and filename ~* '_sunrise'
        """,
            (
                r2 - datetime.timedelta(minutes=30),
                r2 + datetime.timedelta(minutes=45),
                row["id"],
            ),
        )
        cursor2.execute(
            """
            UPDATE webcam_scheduler SET begints = %s, endts = %s WHERE
            cid = %s and filename ~* '_day'
        """,
            (
                r2 - datetime.timedelta(minutes=30),
                s2 + datetime.timedelta(minutes=30),
                row["id"],
            ),
        )

    cursor2.close()
    dbconn.commit()
    dbconn.close()


if __name__ == "__main__":
    main()
