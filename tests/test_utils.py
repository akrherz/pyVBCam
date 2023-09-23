"""Exercise the utils module."""

from pyvbcam import utils


def test_get_camids():
    """Test that we can get camids."""
    utils.get_camids("KCCI")
    utils.get_camids("ALL")
    assert not list(utils.get_camids("FOO"))
