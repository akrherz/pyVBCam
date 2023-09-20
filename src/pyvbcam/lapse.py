"""A lapse"""
import datetime
import logging
import os
import random
import shutil
import subprocess
import sys
import time
from io import BytesIO
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont

import pyvbcam.utils as camutils


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
        req = requests.get(url)
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

            # Set up buffer for image to go to
            buf = BytesIO()

            try:
                drct = self.camera.getDirection()
                imgdata = self.camera.get_one_shot()
                if imgdata is None:
                    time.sleep(10)
                    fails += 1
                    continue
                buf.write(imgdata)
                buf.seek(0)
                img = Image.open(buf)
                draw = ImageDraw.Draw(img)
                fails = 0
            except IOError as exp:
                logging.exception(exp)
                time.sleep(10)
                fails += 1
                continue
            now = datetime.datetime.now()
            (_, imgheight) = img.size

            # Place timestamp on the image
            stamp = "%s   %s" % (
                camutils.dir2text(drct),
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

            img.save("%05i.jpg" % (self.i,))
            self.wait_for_next_frame(self.i)
            del img
            del buf
            self.i += 1

    def wait_for_next_frame(self, i):
        """Sleep logic between frames"""
        delta = self.ets - datetime.datetime.now()
        if delta.days < 0:
            secs_left = 0
        else:
            secs_left = delta.seconds
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
        ffmpeg = "ffmpeg -i %05d.jpg"
        if self.filename != "test":
            # Lets sleep for around 12 minutes,
            # so that we don't have 27 ffmpegs going
            randsleep = 720.0 * random.random()
            logging.info(
                "Sleeping %.2f seconds before launching ffmpeg", randsleep
            )
            time.sleep(randsleep)

        def safe_copy(src, dest):
            """Copy file, safely"""
            try:
                shutil.copyfile(src, "/mesonet/share/lapses/auto/%s" % (dest,))
            except IOError as exp:
                logging.error(exp)

        # 1. Create Flash Video in full res!
        if os.path.isfile("out.flv"):
            os.unlink("out.flv")
        proc = subprocess.Popen(
            "%s -b 1000k out.flv" % (ffmpeg,),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        safe_copy("out.flv", "%s.flv" % (self.filename,))
        # Cleanup after ourself
        os.unlink("out.flv")

        # 2. MP4
        if os.path.isfile("out.mp4"):
            os.unlink("out.mp4")
        proc = subprocess.Popen(
            "%s out.mp4" % (ffmpeg,),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        safe_copy("out.mp4", "%s.mp4" % (self.filename,))
        # Cleanup after ourself
        os.unlink("out.mp4")

        # 3. Create tar file of images
        subprocess.call(
            "tar -cf %s_frames.tar *.jpg" % (self.filename,), shell=True
        )
        safe_copy(
            "%s_frames.tar" % (self.filename,),
            "%s_frames.tar" % (self.filename,),
        )
        # Cleanup after ourselfs
        os.unlink("%s_frames.tar" % (self.filename,))

        # 4. mov files
        if os.path.isfile("out.mov"):
            os.unlink("out.mov")
        proc = subprocess.Popen(
            "%s -b 2000k out.mov" % (ffmpeg,),
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        subprocess.call(
            ("pqinsert -p 'lapse c " "000000000000 %s/%s.qt BOGUS qt' out.mov")
            % (self.network, self.filename),
            shell=True,
        )
        # Cleanup after ourself
        os.unlink("out.mov")
