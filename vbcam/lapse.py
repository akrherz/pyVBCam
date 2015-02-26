
import os
import time
import StringIO
import datetime
import urllib2
import logging
import sys
import shutil
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont
import pytz

import vbcam

class scrape(object):

    def __init__(self, cid, row):
        self.cid = cid
        self.row = row

    def getDirection(self):
        return self.row['pan0']

    def getOneShot(self):
        now = datetime.datetime.now()
        now = now.replace(tzinfo=pytz.timezone("America/Chicago"))

        url = self.row['scrape_url']
        req = urllib2.Request(url)
        req2 = urllib2.urlopen(req)
        modified = req2.info().getheader('Last-Modified')
        if modified:
            gmt = datetime.datetime.strptime(modified, "%a, %d %b %Y %H:%M:%S %Z")
            now = gmt + datetime.timedelta(seconds=now.utcoffset().seconds)
        return req2.read() 


class Lapse(object):
    """
    Represents a timelapse!
    """
    font = ImageFont.truetype('../lib/veramono.ttf', 22)
    sfont = ImageFont.truetype('../lib/veramono.ttf', 14)
    date_height = 370

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

        while self.i < self.frames :
            logging.info("i = %s, fails = %s" % (self.i, fails) )
            if fails > 5:
                logging.info("failed too many times")
                sys.exit(0)

            # Set up buffer for image to go to
            buf = StringIO.StringIO()

            try:
                drct = self.camera.getDirection()
                buf.write( self.camera.getOneShot() )
                buf.seek(0)
                imgdata = Image.open( buf )
                draw = ImageDraw.Draw(imgdata)
                fails = 0
            except IOError, exp:
                logging.exception( exp )
                time.sleep(10)
                fails += 1
                continue
        
            now = datetime.datetime.now()
            
            if self.network != 'KELO':
                stamp = "%s   %s" % (vbcam.drct2dirTxt(drct), 
                                   now.strftime("%-I:%M %p") )
                (width, height) = self.font.getsize(stamp)
                if self.network == 'KCRG2':
                    draw.rectangle( [545-width-10, self.date_height, 545, 
                                     self.date_height+height], fill="#000000" )
                    draw.text((540-width, self.date_height), stamp, 
                              font=self.font)
                else:
                    draw.rectangle( [205-width-10, self.date_height, 205, 
                                     self.date_height+height], fill="#000000" )
                    draw.text((200-width, self.date_height), stamp, 
                              font=self.font)
        
                stamp = "%s" % (now.strftime("%d %b %Y"), )
            else:
                stamp = "%s  %s" % (now.strftime("%d %b %Y %-I:%M %p"), 
                                  vbcam.drct2dirTxt(drct))
            (width, height) = self.sfont.getsize(stamp)
            draw.rectangle( [0, 480-height, 0+width, 480], fill="#000000" )
            draw.text((0, 480-height), stamp, font=self.sfont)
            del draw
        
            imgdata.save('%05i.jpg' % ( self.i,))
            self.wait_for_next_frame(self.i)
            del imgdata
            del buf
            self.i += 1

    def wait_for_next_frame(self, i):
        """
        Sleep logic between frames
        """
        delta = self.ets - datetime.datetime.now()
        if delta.days < 0:
            secs_left = 0
        else:
            secs_left = delta.seconds
        delay = (secs_left -((self.frames - i) * 2)) / (self.frames - i) 
        logging.info("secs_left = %.2f, frames_left = %d, delay = %.2f", 
                     secs_left,  self.frames - i, delay)
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
        ffmpeg = 'ffmpeg -i %05d.jpg'
        # Lets sleep for around 12 minutes, 
        # so that we don't have 27 ffmpegs going 
        randsleep = 720. * random.random()
        logging.info("Sleeping %.2f seconds before launching ffmpeg", 
                     randsleep)
        time.sleep( randsleep )
        
        def safe_copy(src, dest):
            """ Copy file, safely """
            try:
                shutil.copyfile(src, "/mesonet/share/lapses/auto/%s" % (dest,))
            except Exception, exp:
                logging.error(exp)

        # 1. Create Flash Video in full res!
        if os.path.isfile("out.flv"):
            os.unlink("out.flv")
        proc = subprocess.Popen("%s -b 1000k out.flv" % (ffmpeg,), shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        safe_copy("out.flv", "%s.flv" % (self.filename,))
        # Cleanup after ourself
        os.unlink("out.flv")

        # 2. MP4
        if os.path.isfile("out.mp4"):
            os.unlink("out.mp4")
        proc = subprocess.Popen("%s out.mp4" % (ffmpeg,),
                                shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        safe_copy("out.mp4", "%s.mp4" % (self.filename,))
        # Cleanup after ourself
        os.unlink("out.mp4")

        # 3. Create tar file of images
        subprocess.call("tar -cf %s_frames.tar *.jpg" % (self.filename,),
                        shell=True)
        safe_copy("%s_frames.tar" % (self.filename,),
                  "%s_frames.tar" % (self.filename,))
        # Cleanup after ourselfs
        os.unlink("%s_frames.tar" % (self.filename,))

        # KCCI wanted no lapses between 5 and 6:30, OK....
        if self.network == 'KCCI':
            now = datetime.datetime.now()
            if now.hour == 17 or (now.hour == 18 and now.minute < 30):
                endts = now.replace(hour=18, minute=30)
                time.sleep((endts - now).seconds)

                # Lets sleep for around 6 minutes,
                # so that we don't have 27 ffmpegs going
                time.sleep(360. * random.random())

        # 4. mov files
        if os.path.isfile("out.mov"):
            os.unlink("out.mov")
        proc = subprocess.Popen("%s -b 2000k out.mov" % (ffmpeg,),
                                shell=True, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
        logging.info(proc.stdout.read())
        logging.error(proc.stderr.read())
        subprocess.call(("/home/ldm/bin/pqinsert -p 'lapse c "
                         "000000000000 %s/%s.qt BOGUS qt' out.mov") % (
                        self.network, self.filename), shell=True)
        # Cleanup after ourself
        os.unlink("out.mov")
