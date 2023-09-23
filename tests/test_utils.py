"""Exercise the utils module."""

from pyvbcam import utils


def test_get_password():
    """Test the fetching of password from settings.json"""
    assert utils.get_password("KCCI-0001") == "..."
    assert utils.get_password("KELO-0001") == "..."


def test_get_camids():
    """Test that we can get camids."""
    utils.get_camids("KCCI")
    utils.get_camids("ALL")
    assert not list(utils.get_camids("FOO"))
