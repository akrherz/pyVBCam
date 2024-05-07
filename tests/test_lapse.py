"""Test the lapse module."""

from io import BytesIO

from pyvbcam import lapse


def test_lapse_basic():
    """Test the lapse module."""
    lp = lapse.Lapse()
    # Mock lp.camera
    lp.camera = lapse.scrape(1, {"pan0": 0, "scrape_url": "http://localhost"})
    lp.camera.getDirection = lambda: 0
    with open("tests/data/white.png", "rb") as fh:
        payload = fh.read()
    lp.camera.get_one_shot = lambda: payload
    with BytesIO() as buf:
        lp.do_frame(buf)
