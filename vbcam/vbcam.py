"""
 Python Library for Messing with the Canon VB-C10, VB-C50i, VB-C60
"""

import urllib2
import httplib
import re
import string
import traceback
import time
import sys
import logging
import socket

def drct2dirTxt(dir):
  if (dir == None):
    return "N"
  dir = int(dir)
  if (dir >= 350 or dir < 13):
    return "N"
  elif (dir >= 13 and dir < 35):
    return "NNE"
  elif (dir >= 35 and dir < 57):
    return "NE"
  elif (dir >= 57 and dir < 80):
    return "ENE"
  elif (dir >= 80 and dir < 102):
    return "E"
  elif (dir >= 102 and dir < 127):
    return "ESE"
  elif (dir >= 127 and dir < 143):
    return "SE"
  elif (dir >= 143 and dir < 166):
    return "SSE"
  elif (dir >= 166 and dir < 190):
    return "S"
  elif (dir >= 190 and dir < 215):
    return "SSW"
  elif (dir >= 215 and dir < 237):
    return "SW"
  elif (dir >= 237 and dir < 260):
    return "WSW"
  elif (dir >= 260 and dir < 281):
    return "W"
  elif (dir >= 281 and dir < 304):
    return "WNW"
  elif (dir >= 304 and dir < 324):
    return "NW"
  elif (dir >= 324 and dir < 350):
    return "NNW"


class VAPIX:
    """ Class representing access to a VAPIX webcam """

    def __init__(self, cid, row, user, password, res='640x480'):
        self.cid = cid
        self.pan0 = row["pan0"]
        self.ip = row["ip"]
        self.port = row['port']
        self.name = row['name']
        self.settings = {}
        self.res = res

        pm = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pm.add_password(None, "%s:%s" % (row['ip'], row['port']), user,
                        password)
        self.ah = urllib2.HTTPDigestAuthHandler(pm)
        opener = urllib2.build_opener(self.ah)
        urllib2.install_opener(opener)
        self.retries = 6
        self.getSettings()
        self.retries = 60

    def getSettings(self):
        """ Get the current PTZ """
        data = self.http('com/ptz.cgi?query=position')
        if data is None:
            logging.debug("Failed to get settings for ip: %s" % (self.ip,))
            return
        for line in data.split("\n"):
            tokens = line.split("=")
            if len(tokens) == 2:
                self.settings[ tokens[0] ] = tokens[1].strip()

    def dir2pan(self, drct):
        """  Compute a pan based on a given direction, yikes? """
        offset = drct - self.pan0
        if (offset < -180): # We need to go the other way
            offset = (360 + drct) - self.pan0
        elif (offset > 180): # We need to go the other way
            offset = (drct - 360) - self.pan0

        if offset < -179.9:
            offset = -179.9
        if offset > 179.9:
            offset = 179.9
        #print "pan0: %s drct: %s offset: %s" % (self.pan0, drct, offset)
        return offset

    def panDrct(self, drct):
        ''' Turn the webcam to the provided North relative direction '''
        return self.pan( self.dir2pan(drct) )

    def pan(self, deg):
        ''' Pan to the relative to webcam direction '''
        print 'Panning to camera relative: %s deg' % (deg,)
        return self.http('com/ptz.cgi?pan=%.2f' % (deg,))

    def zoom(self, val):
        ''' Zoom to the given zoom '''
        return self.http('com/ptz.cgi?zoom=%s' % (val,))

    def tilt(self, val):
        ''' Tilt '''
        return self.http('com/ptz.cgi?tilt=%s' % (val,))

    def getOneShot(self):
        """ Get a still image """
        return self.http('jpg/image.cgi?resolution=%s' % (self.res, ))

    def getDirection(self):
        """ Get the direction of the current pan """
        deg_pan = float(self.settings['pan']) # in deg
        off = self.pan0 + deg_pan
        if (off < 0):
            off = 360 + off
        if (off >= 360):
            off = off - 360
        return off

    def drct2txt(self, dir):
        
        return drct2dirTxt(dir)

    def realhttp(self, s):
        r = urllib2.urlopen('http://%s:%s/axis-cgi/%s' % (self.ip, self.port, s), 
                            timeout=30 )
        logging.debug("HTTP request => %s, status = %s" % (s, r.code))
        if (r.headers.status != ""):
            logging.debug("HTTP Request Failed: reason %s" % ( r.info() ) )
            data = None
        else:
            data = r.read()
        r.close()
        del r
        return data

    def http(self, s):
        ''' http helper '''
        c = 0
        data = None
        while c < self.retries:
            try:
                data = self.realhttp(s)
                if data is not None:
                    break
            except socket.timeout:
                logging.debug('urllib2 timout!')
            except urllib2.URLError, e:
                logging.debug('urllib2 cmd: %s error: %r retries: %s' % ( s, e, 
                                                    self.retries - c) )
            except httplib.BadStatusLine:
                logging.info('httplib.BadStatusLine from IP: %s (%s)' % (self.ip, 
                                                                    self.name))
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                traceback.print_exc(logging)
            c += 1
        return data

    def closeConnection(self):
        #noop
        pass

class vbcam:

    def __init__(self, id, d, user, passwd, loglevel=logging.WARNING):
        self.error = 0
        self.id = id
        self.d = d
        self.ip = d['ip']
        self.port = d['port']
        self.pan0 = d['pan0']
        self.name = d['name']
        self.settings = {}
        self.cid = None
        self.haveControl = False
        self.log = logging.getLogger(__name__)

        pm = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pm.add_password(None, "%s:%s" % (d['ip'], d['port']) ,user, passwd)
        self.ah = urllib2.HTTPBasicAuthHandler(pm)
        opener = urllib2.build_opener(self.ah)
        urllib2.install_opener(opener)
    
        # Make the initial attempt take less time!
        self.retries = 6
        self.getSettings()
        self.retries = 60


    def closeConnection(self):
        d = self.http("CloseCameraServer?connection_id=%s" % (self.cid,))

    def panDrct(self, drct):
        """ Pan the webcam to this absolute direction """
        return self.pan( self.dir2pan(drct) )

    def pan(self, pan):
        """ pan the camera to this explicit camera relative direction """ 
        self.getControl()
        self.log.debug(' Attempting to pan webcam %.2f degrees' % (pan,))
        return self.http("OperateCamera?connection_id=%s&pan=%i" % (self.cid, 
                                                                 pan *100))

    def zoom(self, zoom):
        self.getControl()
        d = self.http("OperateCamera?connection_id=%s&zoom=%i" % (self.cid, zoom *100))

    def tilt(self, tilt):
        self.getControl()
        d = self.http("OperateCamera?connection_id=%s&tilt=%i" % (self.cid, tilt *100))

    def getOneShot(self):
        return self.http("GetOneShot")
    def getStillImage(self):
        return self.http("GetStillImage")

    def dir2pan(self, drct):
        """  Compute a pan based on a given direction, yikes? """
        offset = drct - self.pan0
        if (offset < -180): # We need to go the other way
            offset = (360 + drct) - self.pan0
        elif (offset > 180): # We need to go the other way
            offset = (drct - 360) - self.pan0
    
        if (offset < -170):
            offset = -170
        if (offset > 170):
            offset = 170
        #print "pan0: %s drct: %s offset: %s" % (self.pan0, drct, offset)
        return offset

    def getTilt(self):
        return float(self.settings['tilt_current_value']) / 100.0

    def getZoom(self):
        return float(self.settings['zoom_current_value']) / 100.0

    def pan2dir(self, pan=None):
        """ Figure out the direction based on a given pan, yikes? """
        if (pan is None and self.settings.has_key('pan_current_value')):
            pan = self.settings['pan_current_value']
        elif (pan is None):
            logging.debug("Don't have pan_current_value set, asumming 0")
            pan = 0
        deg_pan = float(int(pan)) / float(100)
        off = self.pan0 + deg_pan
        if (off < 0):
            off = 360 + off
        if (off >= 360):
            off = off - 360
        return off

    def getDirectionText(self):
        return self.drct2txt( self.getDirection() )

    def getDirection(self):
        self.getSettings()
        return self.pan2dir()

    def getControl(self):
        self.haveControl = False
        if (self.cid == None):
            self.startSession()
    
        for attempt in range(10):
            d = self.http("GetCameraControl?connection_id=%s" % (self.cid,) )
            if (d.strip() == "OK."):
                self.haveControl = True
                break
            self.startSession()
            print "Couldn't get Control. Attempt? %s Answer? %s" % (attempt,d)
      

    def startSession(self):
        d = self.http("OpenCameraServer")
        self.cid = re.findall("connection_id=(.*)", d)[0]

    def getSettings(self):
        d = self.http("GetCameraInfo")
        if (type(d) is not type("a")):
            logging.debug("Failed Get on Settings")
            return
        tokens = re.findall("([^=]*)=([^=]*)\n", d)
        for i in range(len(tokens)):
            self.settings[ tokens[i][0] ] = tokens[i][1]

    def http(self, s):
        """Do a HTTP request

        Args:
          s (str): string URL to request

        Returns:
          data (str): data returned from the HTTP request, could be None
        """
        c = 0
        data = None
        while c < self.retries:
            try:
                data = self.realhttp(s)
                if data is not None:
                    break
            except socket.timeout:
                self.log.debug('urllib2 timout!')
            except urllib2.URLError, e:
                self.log.debug(('urllib2 cmd: %s error: %r retries: %s'
                                '') % (s, e, self.retries - c),
                               exc_info=1)
            except httplib.BadStatusLine:
                self.log.info(('httplib.BadStatusLine from IP: %s (%s)'
                               '') % (self.ip, self.name))
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                self.log.info("Exception has occured", exc_info=1)
            time.sleep(10)  # wait 10 seconds
            c += 1
        return data

    def realhttp(self, s):
        r = urllib2.urlopen('http://%s:%s/-wvhttp-01-/%s' % (self.ip,
                                                             self.port, s),
                            timeout=30)
        self.log.debug("HTTP request => %s, status = %s" % (s, r.code))
        if (r.headers.status != ""):
            self.log.debug("HTTP Request Failed: reason %s" % (r.info()))
            data = None
        else:
            data = r.read()
        r.close()
        del r
        return data

    def drct2txt(self, mydir):
        return drct2dirTxt(mydir)
