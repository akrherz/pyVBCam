"""A basic definition of a webcam object"""
from pywebcam.utils import dir2text


class BasicWebcam(object):
    """An object that allows interaction with a remote webcam"""

    def drct2txt(self, mydir):
        """Convert this direction to text"""
        return dir2text(mydir)
