
import os
import time
import StringIO
import datetime
import urllib2
import logging
import sys
import shutil
import random

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
        
    
    def create_lapse(self):
        """
        Create the timelapse frames, please
        """
        i = 0
        fails = 0
        # Assume 30fps
        
        while i < self.frames :
            logging.info("i = %s, fails = %s" % (i, fails) )
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
        
            imgdata.save('%05i.jpg' % ( i,))
            self.wait_for_next_frame(i)
            del imgdata
            del buf
            i += 1

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
        Postprocess our frames!
        """
        ffmpeg = 'ffmpeg -i %05d.jpg'
        devnull = '< /dev/null >& /dev/null'
        # Lets sleep for around 6 minutes, 
        # so that we don't have 27 ffmpegs going 
        randsleep = 360. * random.random()
        logging.info("Sleeping %.2f seconds before launching ffmpeg", 
                     randsleep)
        time.sleep( randsleep )
        
        # Create something for website
        os.system("%s -s 320x240 -vcodec wmv1 out.wmv %s" % (ffmpeg, devnull))
        shutil.copyfile("out.wmv", "/mesonet/share/lapses/auto/%s.wmv" % (
                                                            self.filename,) )
        
        # Create Flash Video in full res!
        os.system("%s -b 1000k out.flv %s" % (ffmpeg, devnull))
        shutil.copyfile("out.flv", "/mesonet/share/lapses/auto/%s.flv" % (
                                                            self.filename,) )
        
        # Create tar file of images
        os.system("tar -cf %s_frames.tar *.jpg" % (self.filename,) )
        shutil.copyfile("%s_frames.tar" % (self.filename,), 
                        "/mesonet/share/lapses/auto/%s_frames.tar" % (
                                                            self.filename,))
        
        # KCCI wanted no lapses between 5 and 6:30, OK....
        if self.network == 'KCCI':
            now = datetime.datetime.now()
            if now.hour == 17 or (now.hour == 18 and now.minute < 30):
                endts = now.replace(hour=18, minute=30)
                time.sleep( (endts - now).seconds )
            
                # Lets sleep for around 6 minutes, 
                # so that we don't have 27 ffmpegs going 
                time.sleep( 360. * random.random() )
                
        # Create something for KCCI
        os.system("%s -b 2000k out.mov %s" % (ffmpeg, devnull))
        pqinsert = '/home/ldm/bin/pqinsert'
        os.system("%s -p 'lapse c 000000000000 %s/%s.qt BOGUS qt' out.mov" % (
                            pqinsert, self.network, self.filename) )