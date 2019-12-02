"""Update the database to set proper sunrise and sunset times"""
import datetime

import pytz
import ephem
import psycopg2.extras
import pyvbcam.utils as camutils

NOW = datetime.datetime.utcnow()
NOW = NOW.replace(tzinfo=pytz.utc)
NOW = NOW.astimezone(pytz.timezone("America/Chicago"))


def mydate(tstamp):
    """Convert this string to a proper timestamp"""
    if tstamp is None or tstamp == "":
        return datetime.datetime(1989, 1, 1)

    gts = datetime.datetime.strptime(str(tstamp), "%Y/%m/%d %H:%M:%S")
    return gts + datetime.timedelta(seconds=NOW.utcoffset().seconds)


def main():
    """Do things please!"""
    dbconn = psycopg2.connect(
        database=camutils.SETTINGS["database"]["name"],
        host=camutils.SETTINGS["database"]["host"],
    )
    cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor2 = dbconn.cursor()

    sun = ephem.Sun()

    cursor.execute(
        """
        SELECT id, ST_x(geom) as lon, ST_y(geom) as lat from webcams WHERE
        online = 't' and network in ('KELO','KCCI','KCRG','ISUC', 'MCFC')
        """
    )

    for row in cursor:
        ob = ephem.Observer()
        ob.lat = str(row["lat"])
        ob.long = str(row["lon"])
        ob.date = ("%s 10:00") % (
            datetime.datetime.utcnow().strftime("%Y/%m/%d"),
        )
        sun.compute(ob)
        # print row['id'], sun.rise_time, sun.set_time
        r2 = mydate(ob.next_rising(sun))
        s2 = mydate(ob.next_setting(sun))

        sql = """
            UPDATE webcam_scheduler SET
            begints = '%s'::timestamp - '45 minutes'::interval,
            endts = '%s'::timestamp + '45 minutes'::interval WHERE
            cid = '%s' and filename ~* '_eve'
        """ % (
            s2.strftime("%Y-%m-%d %H:%M"),
            s2.strftime("%Y-%m-%d %H:%M"),
            row["id"],
        )
        cursor2.execute(sql)
        sql = """
            UPDATE webcam_scheduler SET
            begints = '%s'::timestamp - '30 minutes'::interval,
            endts = '%s'::timestamp + '45 minutes'::interval WHERE
            cid = '%s' and filename ~* '_sunrise'
        """ % (
            r2.strftime("%Y-%m-%d %H:%M"),
            r2.strftime("%Y-%m-%d %H:%M"),
            row["id"],
        )
        cursor2.execute(sql)
        sql = """
            UPDATE webcam_scheduler SET
            begints = '%s'::timestamp - '30 minutes'::interval,
            endts = '%s'::timestamp + '30 minutes'::interval WHERE
            cid = '%s' and filename ~* '_day'
        """ % (
            r2.strftime("%Y-%m-%d %H:%M"),
            s2.strftime("%Y-%m-%d %H:%M"),
            row["id"],
        )
        cursor2.execute(sql)

    cursor2.close()
    dbconn.commit()
    dbconn.close()


if __name__ == "__main__":
    main()
