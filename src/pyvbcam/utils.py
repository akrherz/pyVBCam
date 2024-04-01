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
