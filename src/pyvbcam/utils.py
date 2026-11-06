"""Some common stuff used by the scripts

Note: It is important that this module not import other parts of this code
"""

import json
import os
from pathlib import Path

from PIL import Image, ImageFile
from pyiem.database import get_dbconnc
from pyiem.util import LOG

DATADIR = os.sep.join([os.path.dirname(__file__), "data"])
SETTINGS = json.load(open("settings.json"))


def get_camids(network):
    """Yield a list of camera IDs for a given network"""
    if network not in ["ALL", "KCCI", "KCRG", "ISUC", "MCFC", "WOI"]:
        LOG.warning("Provided network '%s' is unknown", network)
        return
    networks = (
        ["KCCI", "KCRG", "ISUC", "MCFC", "WOI"]
        if network == "ALL"
        else [network]
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
    return SETTINGS["auth"][camid.split("-")[0]][1]


def get_user(camid):
    """Return the password for a given camera ID"""
    if SETTINGS["auth"].get(camid):
        return SETTINGS["auth"][camid][0]
    return SETTINGS["auth"][camid.split("-")[0]][0]


def overlay_logo(img: ImageFile):
    """Overlay the WOI logo on the image"""
    logo_path = Path(__file__).parent / "data" / "WOI.png"
    if not logo_path.is_file():
        LOG.info("Logo %s not found", logo_path)
        return
    with Image.open(logo_path) as logo:
        resized = logo.convert("RGBA").resize((318, 85), Image.LANCZOS)
        img.paste(resized, (5, 980), resized)
