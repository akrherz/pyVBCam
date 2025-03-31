"""Exercise the utils module."""

from pyvbcam import utils


def test_get_password():
    """Test the fetching of password from settings.json"""
    assert utils.get_password("KELO-0001") == "..."


def test_get_camids():
    """Test that we can get camids."""
    assert list(utils.get_camids("KCCI"))
    assert list(utils.get_camids("ALL"))
    assert not list(utils.get_camids("FOO"))
