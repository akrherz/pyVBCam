"""
  Drives the production of auto timed webcam lapses
"""
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

import datetime
import time
import subprocess
import psycopg2
import psycopg2.extras
dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (config.get('database', 'host'),
                                              config.get('database', 'user'),
                                              config.get('database', 'name')))
cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

import sys
import os

sys.path.insert(0, '../vbcam/')
import vbcam

import time
import StringIO
import datetime
from PIL import Image, ImageDraw, ImageFont
import shutil, random
import logging
import urllib2

from pyiem import iemtz

class scrape(object):
    
    def __init__(self, cid, row):
        self.cid = cid
        self.row = row
        
    def getDirection(self):
        return self.row['pan0']
    
    def getOneShot(self):
        now = datetime.datetime.now()
        now = now.replace(tzinfo=iemtz.Central)

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
            logging.info("i = %s", (i,) )
            if fails > 10:
                sys.exit(0)
        
            # Set up buffer for image to go to
            buf = StringIO.StringIO()
            drct = self.camera.getDirection()
            buf.write( self.camera.getOneShot() )
            buf.seek(0)
            try:
                imgdata = Image.open( buf )
                draw = ImageDraw.Draw(imgdata)
            except IOError, exp:
                logging.debug( exp )
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
        secs_left = (self.ets - datetime.datetime.now()).seconds
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
        shutil.copyfile("out.wmv", "/mnt/mesonet/share/lapses/auto/%s.wmv" % (
                                                            self.filename,) )
        
        # Create Flash Video in full res!
        os.system("%s -b 1000k out.flv %s" % (ffmpeg, devnull))
        shutil.copyfile("out.flv", "/mnt/mesonet/share/lapses/auto/%s.flv" % (
                                                            self.filename,) )
        
        # Create tar file of images
        os.system("tar -cf %s_frames.tar *.jpg" % (self.filename,) )
        shutil.copyfile("%s_frames.tar" % (self.filename,), 
                        "/mnt/mesonet/share/lapses/auto/%s_frames.tar" % (
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


def setup_job(job):
    """
    Setup our lapse job
    """
    job.init_delay = int(sys.argv[1])
    job.site = sys.argv[2]
    job.network = job.site[:4]
    job.secs = int(float(sys.argv[3]))
    job.filename = sys.argv[4]
    job.movie_duration = int(float(sys.argv[5]))
    job.frames = job.movie_duration * 30

    outdir = "../tmp/autoframes.%s_%s" % (job.filename, 
                                   datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    os.makedirs(outdir)
    os.chdir(outdir)

    logging.basicConfig(filename="%s.log" % (job.site, ), filemode='w',
                    format='%(levelname)s: %(asctime)-15s %(message)s', 
                    level=logging.DEBUG )
    logging.info("We are off and running!")

def bootstrap(job):
    """
    Get us off and running!
    """
    cursor.execute("""SELECT * from webcams where id = %s""", (job.site,) )
    row = cursor.fetchone()
    if row['scrape_url'] is None:
        network = row['network']
        password = config.get(network, 'password')
        user = config.get(network, 'user')
        if config.has_section(job.site):
            password = config.get(job.site, 'password')
            user = config.get(job.site, 'user')
        
        job.camera = vbcam.vbcam(job.site, row, user, password)
        cursor.close()
        dbconn.close()
    
        if job.camera.settings == {}:
            logging.info("Failed to reach camera, aborting...")
            sys.exit(0)
    else:
        job.camera = scrape(job.site, row)

    # Initially sleep until it is go time!
    logging.debug("Initial sleep of: %s", job.init_delay)
    time.sleep(job.init_delay + random.random() )

    # compute
    sts = datetime.datetime.now()
    job.ets = sts + datetime.timedelta(seconds = job.secs)

if __name__ == '__main__':
    JOB = Lapse()
    setup_job(JOB)
    bootstrap(JOB)
    JOB.create_lapse()
    JOB.postprocess()
    logging.info("Done!")
