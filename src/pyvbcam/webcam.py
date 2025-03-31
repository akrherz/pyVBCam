"""A basic definition of a webcam object"""

import logging
import sys

import httpx
from pyiem.util import drct2text

from pyvbcam import WebCamConfig


class BasicWebcam:
    """An object that allows interaction with a remote webcam"""

    PREFIX = ""

    def __init__(self, config: WebCamConfig):
        """The constructor"""
        # hold the config object
        self.config = config
        self.webbase = (
            f"http://{config.ip if config.fqdn is None else config.fqdn}:"
            f"{config.port}"
        )
        self.httpauth = httpx.DigestAuth(config.username, config.password)
        self.settings = {}
        self.retries = 6
        self.connid = None
        self.haveControl = False

        self.log = logging.getLogger(__name__)

        self.getSettings()

    def getSettings(self):
        """overide me"""
        raise NotImplementedError

    def drct2txt(self, mydir):
        """Convert this direction to text"""
        return drct2text(mydir)

    def realhttp(self, s):
        """Make a real connection"""
        req = httpx.get(
            f"{self.webbase}{self.PREFIX}/{s}",
            auth=self.httpauth,
            timeout=30,
        )
        logging.debug("HTTP request => %s, status = %s", s, req.status_code)
        if req.status_code == 401 and isinstance(
            self.httpauth, httpx.DigestAuth
        ):
            logging.debug("downgrading HTTPAuth to Basic")
            self.httpauth = httpx.BasicAuth(
                self.config.username, self.config.password
            )
            req = httpx.get(
                f"{self.webbase}{self.PREFIX}/{s}",
                auth=self.httpauth,
                timeout=30,
            )
            logging.debug(
                "HTTP request => %s, status = %s", s, req.status_code
            )
        if req.status_code != 200:
            return None
        return req.content

    def http(self, s):
        """http helper"""
        c = 0
        data = None
        while c < 6:
            try:
                data = self.realhttp(s)
                if data is not None:
                    break
            except httpx.ConnectTimeout:
                logging.debug("request timout!")
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as exp:
                logging.debug(repr(exp))
            c += 1
        return data
