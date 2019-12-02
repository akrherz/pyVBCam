"""Walk before we crawl."""
from pyvbcam import util


def test_import():
    """Can we import ourself?"""
    assert util is not None
