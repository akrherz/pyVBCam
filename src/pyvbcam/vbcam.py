"""
Python Library for Messing with the Canon VB-C10, VB-C50i, VB-C60
"""

import logging
import re
import time

from pyiem.database import sql_helper, with_sqlalchemy_conn
from sqlalchemy.engine import Connection

import pyvbcam.utils as camutils
from pyvbcam import WebCamConfig
from pyvbcam.webcam import BasicWebcam


@with_sqlalchemy_conn("mesosite")
def get_vbcam(camid: str, conn: Connection = None, settings: dict = None):
    """Return a vbcam object for this camera ID"""
    res = conn.execute(
        sql_helper("""
        SELECT *, ST_x(geom) as lon, ST_y(geom) as lat
        from webcams where id = :cid
    """),
        {"cid": camid},
    )
    row = res.mappings().fetchone()
    cfg = WebCamConfig(
        cid=camid,
        fqdn=row["fqdn"],
        ip=row["ip"],
        lat=row["lat"],
        lon=row["lon"],
        name=row["name"],
        pan0=row["pan0"],
        password=camutils.get_password(camid),
        port=row["port"],
        res=row["fullres"],
        username=camutils.get_user(camid),
    )
    return (VAPIX if row["is_vapix"] else VBCam)(cfg, settings=settings)


class VAPIX(BasicWebcam):
    """Class representing access to a VAPIX webcam"""

    PREFIX = "/axis-cgi"

    def getSettings(self):
        """Get the current PTZ"""
        data = self.http("com/ptz.cgi?query=position")
        if data is None:
            logging.debug("Failed to get settings for: %s", self)
            return
        for line in data.decode("ascii", "ignore").split("\n"):
            tokens = line.split("=")
            if len(tokens) == 2:
                self.settings[tokens[0]] = tokens[1].strip()

    def dir2pan(self, drct):
        """Compute a pan based on a given direction, yikes?"""
        offset = drct - self.config.pan0
        if offset < -180:  # We need to go the other way
            offset = (360 + drct) - self.config.pan0
        elif offset > 180:  # We need to go the other way
            offset = (drct - 360) - self.config.pan0

        if offset < -179.9:
            offset = -179.9
        if offset > 179.9:
            offset = 179.9
        return offset

    def panDrct(self, drct):
        """Turn the webcam to the provided North relative direction"""
        return self.pan(self.dir2pan(drct))

    def pan(self, deg):
        """Pan to the relative to webcam direction"""
        self.log.info("Panning to camera relative: %s deg", deg)
        return self.http(f"com/ptz.cgi?pan={deg:.2f}")

    def zoom(self, val):
        """Zoom to the given zoom"""
        return self.http("com/ptz.cgi?zoom=%s" % (val,))

    def tilt(self, val):
        """Tilt"""
        return self.http("com/ptz.cgi?tilt=%s" % (val,))

    def get_one_shot(self, res: str = None):
        """Get a still image"""
        if res is None:
            res = self.config.res
        return self.http(
            f"jpg/image.cgi?clock=0&date=0&text=0&resolution={res}"
        )

    def getDirection(self):
        """Get the direction of the current pan"""
        if "pan" not in self.settings:
            self.log.debug(
                "%s pan was missing from settings, using pan0/zero",
                self.config.cid,
            )
            return self.config.pan0
        deg_pan = float(self.settings["pan"])  # in deg
        off = self.config.pan0 + deg_pan
        if off < 0:
            off = 360 + off
        if off >= 360:
            off = off - 360
        return off

    def closeConnection(self):
        """nothing to do here as we are stateless with VAPIX"""
        return


class VBCam(BasicWebcam):
    """Canon VB-Webcam"""

    PREFIX = "/-wvhttp-01-"

    def closeConnection(self):
        """Drop the lock we have going with the server"""
        self.http("CloseCameraServer?connection_id=%s" % (self.connid,))

    def panDrct(self, drct):
        """Pan the webcam to this absolute direction"""
        return self.pan(self.dir2pan(drct))

    def pan(self, pan):
        """pan the camera to this explicit camera relative direction"""
        self.getControl()
        self.log.debug(" Attempting to pan webcam %.2f degrees", pan)
        return self.http(
            "OperateCamera?connection_id=%s&pan=%i" % (self.connid, pan * 100)
        )

    def zoom(self, zoom):
        """Zoom the webcam!"""
        self.getControl()
        self.http(
            ("OperateCamera?connection_id=%s&zoom=%i")
            % (self.connid, zoom * 100)
        )

    def tilt(self, tilt):
        """Tilt the webcam!"""
        self.getControl()
        self.http(
            ("OperateCamera?connection_id=%s&tilt=%i")
            % (self.connid, tilt * 100)
        )

    def get_one_shot(self, res: str = None):
        """Get one shot which is more forgiving that GetStillImage"""
        return self.http("GetOneShot")

    def getStillImage(self):
        """Requires more control on the webcam."""
        return self.http("GetStillImage")

    def dir2pan(self, drct):
        """Compute a pan based on a given direction, yikes?"""
        offset = drct - self.config.pan0
        if offset < -180:  # We need to go the other way
            offset = (360 + drct) - self.config.pan0
        elif offset > 180:  # We need to go the other way
            offset = (drct - 360) - self.config.pan0

        if offset < -170:
            offset = -170
        if offset > 170:
            offset = 170
        return offset

    def getTilt(self):
        """Get the current tilt."""
        return float(self.settings["tilt_current_value"]) / 100.0

    def getZoom(self):
        """Get the current zoom."""
        return float(self.settings["zoom_current_value"]) / 100.0

    def pan2dir(self, pan=None):
        """Figure out the direction based on a given pan, yikes?"""
        if pan is None and "pan_current_value" in self.settings:
            pan = self.settings["pan_current_value"]
        elif pan is None:
            logging.debug("Don't have pan_current_value set, asumming 0")
            pan = 0
        deg_pan = float(int(pan)) / float(100)
        off = self.config.pan0 + deg_pan
        if off < 0:
            off = 360 + off
        if off >= 360:
            off = off - 360
        return off

    def getDirectionText(self):
        """Get the current webcam pointing direction."""
        return self.drct2txt(self.getDirection())

    def getDirection(self):
        """Get the current webcam pointing direction."""
        self.getSettings()
        return self.pan2dir()

    def getControl(self):
        """Grab control of the webcam for this session."""
        self.haveControl = False

        for _ in range(10):
            if self.connid is None:
                self.startSession()
            if self.connid is None:
                time.sleep(5)
            else:
                break
        for attempt in range(10):
            d = self.http("GetCameraControl?connection_id=%s" % (self.connid,))
            if d.decode("ascii").strip() == "OK.":
                self.haveControl = True
                break
            self.startSession()
            print(
                ("Couldn't get Control. Attempt? %s Answer? %s") % (attempt, d)
            )

    def startSession(self):
        """Start a control session"""
        d = self.http("OpenCameraServer").decode("ascii")
        if d.find("connection_id=") > -1:
            self.connid = re.findall("connection_id=(.*)", d)[0]
        else:
            self.log.debug("Got invalid response for OpenCameraServer")

    def getSettings(self):
        """return the current camera settings as a dict"""
        d = self.http("GetCameraInfo")
        if d is None:
            logging.debug("Failed to get current settings")
            return
        d = d.decode("ascii", "ignore")
        tokens = re.findall("([^=]*)=([^=]*)\n", d)
        for key, value in tokens:
            self.settings[key] = value
