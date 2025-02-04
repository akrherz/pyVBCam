"""A basic definition of a webcam object"""

import logging
import sys

import requests
from pyiem.util import drct2text


class BasicWebcam:
    """An object that allows interaction with a remote webcam"""

    PREFIX = ""

    def __init__(self, cid, row, user, password):
        """The constructor"""
        self.cid = cid
        self.pan0 = row["pan0"]
        self.ip = row["ip"]
        self.fqdn = row["fqdn"]
        self.port = row["port"]
        self.name = row["name"]
        self.settings = {}
        self.res = row["fullres"]
        self.lat = row["lat"]
        self.lon = row["lon"]
        self.log = logging.getLogger(__name__)

        self.httpauth = requests.auth.HTTPDigestAuth(user, password)
        self.retries = 6
        self.connid = None
        self.haveControl = False
        self.getSettings()

    def getSettings(self):
        """overide me"""
        raise NotImplementedError

    def drct2txt(self, mydir):
        """Convert this direction to text"""
        return drct2text(mydir)

    def realhttp(self, s):
        """Make a real connection"""
        req = requests.get(
            "http://%s:%s/%s/%s"
            % (
                self.ip if self.ip is not None else self.fqdn,
                self.port,
                self.PREFIX,
                s,
            ),
            auth=self.httpauth,
            timeout=30,
        )
        logging.debug("HTTP request => %s, status = %s", s, req.status_code)
        if req.status_code == 401 and isinstance(
            self.httpauth, requests.auth.HTTPDigestAuth
        ):
            logging.debug("downgrading HTTPAuth to Basic")
            self.httpauth = requests.auth.HTTPBasicAuth(
                self.httpauth.username, self.httpauth.password
            )
            req = requests.get(
                "http://%s:%s/%s/%s"
                % (
                    self.ip if self.ip is not None else self.fqdn,
                    self.port,
                    self.PREFIX,
                    s,
                ),
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
            except requests.exceptions.ConnectTimeout:
                logging.debug("requests timout!")
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as exp:
                logging.debug(repr(exp))
            c += 1
        return data
