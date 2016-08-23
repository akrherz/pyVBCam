
import json
import psycopg2.extras
import logging
import sys
sys.path.insert(0, '../vbcam')
import vbcam

settings = json.load(open('settings.json'))


def get_dbconn():
    """ Return a database cursor """
    return psycopg2.connect(database=settings['database']['name'],
                            user=settings['database']['user'],
                            host=settings['database']['host'])


def get_vbcam(camid, loglevel=logging.INFO):
    """ Return a vbcam object for this camera ID """
    PGCONN = get_dbconn()
    cursor = PGCONN.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""SELECT *, ST_x(geom) as lon, ST_y(geom) as lat
        from webcams where id = %s """, (camid,))
    row = cursor.fetchone()
    PGCONN.close()
    if row["is_vapix"]:
        if camid == 'ISUC-002':
            return vbcam.VAPIX(camid, row, get_user(camid),
                               get_password(camid), '704x480')
        return vbcam.VAPIX(camid, row, get_user(camid), get_password(camid))
    else:
        return vbcam.vbcam(camid, row, get_user(camid), get_password(camid),
                           loglevel=loglevel)


def get_password(camid):
    """ Return the password for a given camera ID """
    if settings['auth'].get(camid):
        return settings['auth'][camid][1]
    return settings['auth'][camid[:4]][1]


def get_user(camid):
    """ Return the password for a given camera ID """
    if settings['auth'].get(camid):
        return settings['auth'][camid][0]
    return settings['auth'][camid[:4]][0]
