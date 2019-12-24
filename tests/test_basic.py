"""Walk before we crawl."""
from pyvbcam import utils
from pyvbcam import lapse
from pyvbcam import webcam
from pyvbcam import vbcam


def test_import():
    """Can we import ourself?"""
    assert utils is not None
    assert lapse.scrape is not None
    assert webcam.BasicWebcam is not None
    assert vbcam.BasicWebcam is not None
