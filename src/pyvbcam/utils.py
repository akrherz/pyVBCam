"""Some common stuff used by the scripts

    Note: It is important that this module not import other parts of this code
"""
import json
import os

from pyiem.util import LOG, get_dbconnc

DATADIR = os.sep.join([os.path.dirname(__file__), "data"])
SETTINGS = json.load(open("settings.json"))


def get_camids(network):
    """Yield a list of camera IDs for a given network"""
    if network not in ["ALL", "KCCI", "KCRG", "ISUC", "MCFC"]:
        LOG.warning("Provided network '%s' is unknown", network)
        return
    networks = (
        ["KCCI", "KCRG", "ISUC", "MCFC"] if network == "ALL" else [network]
    )
    dbconn, cursor = get_dbconnc("mesosite")
    cursor.execute(
        "SELECT id from webcams where network = ANY(%s) "
        "and online ORDER by id ASC",
        (networks,),
    )
    for row in cursor:
        yield row["id"]
    dbconn.close()


def get_password(camid):
    """Return the password for a given camera ID"""
    if SETTINGS["auth"].get(camid):
        return SETTINGS["auth"][camid][1]
    return SETTINGS["auth"][camid[:4]][1]


def get_user(camid):
    """Return the password for a given camera ID"""
    if SETTINGS["auth"].get(camid):
        return SETTINGS["auth"][camid][0]
    return SETTINGS["auth"][camid[:4]][0]


def dir2text(mydir):
    """Convert a direction to its plain text equivalent"""
    if mydir is None:
        return "N"
    mydir = int(mydir)
    if mydir >= 350 or mydir < 13:
        return "N"
    elif mydir >= 13 and mydir < 35:
        return "NNE"
    elif mydir >= 35 and mydir < 57:
        return "NE"
    elif mydir >= 57 and mydir < 80:
        return "ENE"
    elif mydir >= 80 and mydir < 102:
        return "E"
    elif mydir >= 102 and mydir < 127:
        return "ESE"
    elif mydir >= 127 and mydir < 143:
        return "SE"
    elif mydir >= 143 and mydir < 166:
        return "SSE"
    elif mydir >= 166 and mydir < 190:
        return "S"
    elif mydir >= 190 and mydir < 215:
        return "SSW"
    elif mydir >= 215 and mydir < 237:
        return "SW"
    elif mydir >= 237 and mydir < 260:
        return "WSW"
    elif mydir >= 260 and mydir < 281:
        return "W"
    elif mydir >= 281 and mydir < 304:
        return "WNW"
    elif mydir >= 304 and mydir < 324:
        return "NW"
    elif mydir >= 324 and mydir < 350:
        return "NNW"
