"""Walk before we crawl."""
from pyvbcam import utils


def test_import():
    """Can we import ourself?"""
    assert utils is not None
