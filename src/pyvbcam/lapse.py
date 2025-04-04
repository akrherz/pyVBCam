"""A lapse"""

import datetime
import glob
import logging
import os
import shutil
import subprocess
import sys
import time
from io import BytesIO
from zoneinfo import ZoneInfo

import httpx
from PIL import Image, ImageDraw, ImageFont
from pyiem.util import drct2text, utc

import pyvbcam.utils as camutils


def safe_copy(src, dest):
    """Copy file, safely"""
    try:
        shutil.copyfile(src, f"/mesonet/share/lapses/auto/{dest}")
    except IOError as exp:
        logging.error(exp)


class scrape(object):
    """This is a vanilla scrapper"""

    def __init__(self, cid, row):
        """Constructor"""
        self.cid = cid
        self.row = row

    def getDirection(self):
        """We have no options to get camera metadata"""
        return self.row["pan0"]

    def get_one_shot(self):
        """Our primary means to get data"""
        now = datetime.datetime.now()
        now = now.replace(tzinfo=ZoneInfo("America/Chicago"))

        url = self.row["scrape_url"]
        req = httpx.get(url)
        modified = req.headers.get("Last-Modified")
        if modified:
            gmt = datetime.datetime.strptime(
                modified, "%a, %d %b %Y %H:%M:%S %Z"
            )
            now = gmt + datetime.timedelta(seconds=now.utcoffset().seconds)
        return req.content


class Lapse(object):
    """Represents a timelapse"""

    font = ImageFont.truetype(camutils.DATADIR + "/veramono.ttf", 22)
    sfont = ImageFont.truetype(camutils.DATADIR + "/veramono.ttf", 14)

    def __init__(self):
        """
        Constructor
        """
        self.camera = None
        self.ets = None
        self.frames = None
        self.init_delay = None
        self.movie_duration = None
        self.filename = None
        self.network = None
        self.site = None
        self.i = 0

    def do_frame(self, buf):
        """Do a single frame"""
        drct = self.camera.getDirection()
        imgdata = self.camera.get_one_shot()
        if imgdata is None:
            raise Exception("Failed to get image data")
        buf.write(imgdata)
        buf.seek(0)
        with Image.open(buf) as img:
            draw = ImageDraw.Draw(img)
            now = datetime.datetime.now()
            (_, imgheight) = img.size

            # Place timestamp on the image
            stamp = "%s   %s" % (
                drct2text(drct),
                now.strftime("%-I:%M %p"),
            )
            labelpt = (125, imgheight - 90)
            bbox = draw.textbbox(labelpt, stamp, font=self.font, anchor="mm")
            height = bbox[3] - bbox[1]
            width = bbox[2] - bbox[0]
            draw.rectangle(
                [
                    labelpt[0] - width / 2.0 - 5,
                    labelpt[1] - height / 2.0 - 5,
                    labelpt[0] + width / 2.0 + 5,
                    labelpt[1] + height / 2.0 + 5,
                ],
                fill="#000000",
            )
            draw.text(labelpt, stamp, font=self.font, anchor="mm")
            del draw

            img.save(f"{self.i:05.0f}.jpg")

    def create_lapse(self):
        """
        Create the timelapse frames, please
        """
        fails = 0
        # Assume 30fps

        while self.i < self.frames:
            logging.info("i = %s, fails = %s", self.i, fails)
            if fails > 5:
                logging.info("failed too many times")
                sys.exit(0)
            try:
                with BytesIO() as buf:
                    self.do_frame(buf)
                self.i += 1
                self.wait_for_next_frame(self.i)
                fails = 0  # reset counter
            except Exception as exp:
                logging.exception(exp)
                fails += 1
                time.sleep(10)

    def wait_for_next_frame(self, i):
        """Sleep logic between frames"""
        secs_left = max((self.ets - utc()).total_seconds(), 0)
        if self.frames - i == 0:
            delay = 0
        else:
            delay = (secs_left - ((self.frames - i) * 2)) / (self.frames - i)
        logging.info(
            "secs_left = %.2f, frames_left = %d, delay = %.2f",
            secs_left,
            self.frames - i,
            delay,
        )
        if delay > 0:
            time.sleep(delay)

    def postprocess(self):
        """
        Postprocess our individual frames into products
        1. .flv for web clients that only can do flash
        2. .mp4 for html5 web clients
        3. .tar file of the frames
        4. .mov for TV stations video system
        """
        # 1. Create Flash Video in full res!
        if os.path.isfile("out.flv"):
            os.unlink("out.flv")
        with subprocess.Popen(
            ["ffmpeg", "-i", "%05d.jpg", "-b", "1000k", "out.flv"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as proc:
            logging.info(proc.stdout.read())
            logging.error(proc.stderr.read())
            # NB: ffmpeg exit code is not reliable
        # belt and suspenders
        if not os.path.isfile("out.flv"):
            logging.error("Failed to create out.flv")
            return
        safe_copy("out.flv", f"{self.filename}.flv")
        # Cleanup after ourself
        os.unlink("out.flv")

        # 2. MP4
        if os.path.isfile("out.mp4"):
            os.unlink("out.mp4")
        proc = subprocess.Popen(
            ["ffmpeg", "-i", "%05d.jpg", "out.mp4"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        safe_copy("out.mp4", f"{self.filename}.mp4")
        # Cleanup after ourself
        os.unlink("out.mp4")

        # 3. Create tar file of images
        subprocess.call(
            ["tar", "-cf", f"{self.filename}_frames.tar", *glob.glob("*.jpg")]
        )
        safe_copy(
            f"{self.filename}_frames.tar",
            f"{self.filename}_frames.tar",
        )
        # Cleanup after ourselfs
        os.unlink(f"{self.filename}_frames.tar")

        # 4. mov files
        if os.path.isfile("out.mov"):
            os.unlink("out.mov")
        proc = subprocess.Popen(
            ["ffmpeg", "-i", "%05d.jpg", "-b", "2000k", "out.mov"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        os.unlink("out.mov")
