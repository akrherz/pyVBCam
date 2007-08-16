
import os
import time
import StringIO
from PIL import Image, ImageDraw, ImageFont
import mx.DateTime

class lapse:

    def __init__(self, camera, delay=10, basedirectory="./", 
      fontfile='LTe50874.ttf'):
        self.ok = 1
        self.camera = camera
        self.delay = delay
        if (basedirectory != None):
            self.directory = "%s/frames.%s.%s"%(basedirectory, self.camera.id,\
             mx.DateTime.now().strftime("%Y%m%d%H%M") )
            self.setup()
        self.cnt = 0
        # Controlbacks
        self.cbControls = []
        # Drawbacks
        self.cbDraws = []
        self.font = ImageFont.truetype(fontfile, 22)
        self.font12 = ImageFont.truetype(fontfile, 12)
        self.font14 = ImageFont.truetype(fontfile, 14)
        self.targetDrct = None
        self.targetTime = None

    def setTarget(self, drct, ts=None):
        """ Set a point and direction in time that we need to get to by... """
        now = mx.DateTime.now()
        if (ts == None):  # Go immediately!
            self.camera.panDrct( drct )
            return
        self.targetTime = ts
        self.targetDrct = drct

    def trackTarget(self):
        print "self.targetTime: %s self.targetDrct %s" % (self.targetTime, self.targetDrct)
        now = mx.DateTime.now()
        if (self.targetTime < now):
            return
        steps = float(self.targetTime - now) / (float(self.delay) +3.0)
        if (steps == 0):
            return
        cdir = self.camera.getDirection()
        offset = (self.targetDrct - cdir) / steps
        print "steps: %s offset: %s" % (steps, offset)
        self.camera.panDrct( cdir + offset )

    def addControl(self, f):
        """ Add a control callback """
        self.cbControls.append( f )

    def addDraw(self, f):
        """ Add a drawing callback """
        self.cbDraws.append( f )

    def setup(self):
        """  Setup the directory for output images to be placed..."""
        if (not os.path.isdir(self.directory)):
            os.makedirs(self.directory)

    def run(self):
        while (self.ok):
            self.step()
            time.sleep(self.delay)

    def loadStillImage(self):
        """ Get latest still image from the camera """ 
        buf = StringIO.StringIO()
        buf.write( self.camera.getStillImage() )
        buf.seek(0)
        self.frame = Image.open( buf )
        buf.seek(0)
        self.orig = Image.open( buf )
        del buf

    def step(self):
        """ Move on in time, grab the image, draw stuff on it """
        # Call Controls
        for c in self.cbControls:
            apply( c )
        self.loadStillImage()
        # Call Draws
        for c in self.cbDraws:
            apply( c )
        self.frame.save('%s/%05i.jpg' % (self.directory, self.cnt) )
        del self.frame
        self.cnt += 1

    def drawStamp(self):
        now = mx.DateTime.now()
        str = "%s   %s" % (self.camera.getDirectionText(), now.strftime("%-I:%M %p") )
        (w, h) = self.font.getsize(str)

        draw = ImageDraw.Draw(self.frame)
        draw.rectangle( [205-w-20,370,205,370+h], fill="#000000" )
        draw.text((200-w,370), str, font=self.font)
        del draw

    def drawCaption(self):
        now = mx.DateTime.now()
        str = "%s [%s] %s" % (self.camera.d['name'], self.camera.getDirectionText(), now.strftime("%d %b %Y %-I:%M %p") )
        (w, h) = self.font12.getsize(str)

        draw = ImageDraw.Draw(self.frame)
        draw.rectangle( [0,480-h,0+w,480], fill="#000000" )
        draw.text((1,480-h), str, font=self.font12)
        del draw

    def stdwxh(self, width=320, height=240, fn=None):
        if (fn == None): fn = "%s.jpg" % (self.camera.id, )
        c = self.orig.resize((width,height))
        # Draw Caption
        now = mx.DateTime.now()
        str = "%s [%s] %s" % (self.camera.d['name'], self.camera.getDirectionText(), now.strftime("%d %b %Y %-I:%M %p") )
        (w, h) = self.font14.getsize(str)

        draw = ImageDraw.Draw(c)
        draw.rectangle( [0,height-h,0+w,height], fill="#000000" )
        draw.text((1,height-h), str, font=self.font14)
        del draw


        c.save(fn)
        del c


    def drawTarget(self):
        """ I will draw an '+' on the screen where I am targetting"""
        drct = float(self.camera.getDirection())
        zoom = self.camera.getZoom()
        tilt = self.camera.getTilt()

        leftedge_pan = drct - (zoom/2.0)
        rightedge_pan = drct + (zoom/2.0)
        dx = ((rightedge_pan - leftedge_pan) / 640.0) 
        if (self.targetDrct < leftedge_pan):
            drawx=2
        elif (self.targetDrct > rightedge_pan):
            drawx=638
        else:
            drawx = (self.targetDrct - leftedge_pan) / dx

        print "lp: %s rp: %s drawx: %s target: %s" % (leftedge_pan, rightedge_pan,drawx, self.targetDrct)
        draw = ImageDraw.Draw(self.frame)
        draw.rectangle( [drawx-2,238,drawx+2,242], fill="#ffffff" )
        del draw
        
