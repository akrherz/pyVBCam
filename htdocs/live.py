"""Generate a 'Live' webcam image on demand

URIs look like so:
    /live.py?id=KCRG-006
    /live/KCRG-006.jpg
"""

import datetime
from io import BytesIO

import httpx
from paste.request import parse_formvars
from PIL import Image, ImageDraw
from pyiem.util import get_dbconnc, get_properties
from pymemcache.client import Client


def fetch(cid):
    """Do work to get the content"""
    # Get camera metadata
    pgconn, cursor = get_dbconnc("mesosite")
    cursor.execute(
        "SELECT ip, fqdn, online, name, port, is_vapix, scrape_url, network "
        "from webcams WHERE id = %s",
        (cid,),
    )
    if cursor.rowcount != 1:
        pgconn.close()
        return
    row = cursor.fetchone()
    pgconn.close()
    ip = row["ip"]
    fqdn = row["fqdn"]
    online = row["online"]
    name = row["name"]
    port = row["port"]
    is_vapix = row["is_vapix"]
    scrape_url = row["scrape_url"]
    network = row["network"]
    if scrape_url is not None or not online:
        return
    # Get IEM properties
    iemprops = get_properties()
    user = iemprops.get(f"webcam.{network.lower()}.user")
    passwd = iemprops.get(f"webcam.{network.lower()}.pass")
    # Construct URI
    uribase = "http://%s:%s/-wvhttp-01-/GetOneShot"
    if is_vapix:
        uribase = "http://%s:%s/axis-cgi/jpg/image.cgi"
    uri = uribase % (ip if ip is not None else fqdn, port)
    ham = (
        httpx.BasicAuth
        if cid
        in [
            "KCRG-010",
        ]
        else httpx.DigestAuth
    )
    req = httpx.get(uri, auth=ham(user, passwd), timeout=15)
    if req.status_code != 200:
        return
    image = Image.open(BytesIO(req.content))
    (width, height) = image.size
    # Draw black box
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, height - 12, width, height], fill="#000000")
    stamp = datetime.datetime.now().strftime("%d %b %Y %I:%M:%S %P")
    title = f"{name} - {network} Webcam Live Image at {stamp}"
    draw.text((5, height - 12), title)
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def workflow(cid):
    """The necessary workflow for this camera ID"""
    mckey = f"/current/live/{cid}.jpg"
    mc = Client("iem-memcached:11211")
    res = mc.get(mckey)
    if res:
        return res
    try:
        res = fetch(cid)
    except Exception as exp:  # noqa
        print(cid, exp)
        return None
    if res is not None:
        # Set for 15 seconds
        mc.set(mckey, res, 15)
    mc.close()
    return res


def application(environ, start_response):
    """Do Fun Things"""
    form = parse_formvars(environ)
    cid = form.get("id", "KCCI-027")[:10]  # Default to Ag Farm
    imagedata = workflow(cid)
    if imagedata is None:
        # TOOD: make a sorry image
        image = Image.new("RGB", (640, 480))
        draw = ImageDraw.Draw(image)
        draw.text((320, 240), "Sorry, failed to generate image :(")
        buf = BytesIO()
        image.save(buf, format="JPEG")
        imagedata = buf.getvalue()

    start_response("200 OK", [("Content-type", "image/jpeg")])
    return [imagedata]
