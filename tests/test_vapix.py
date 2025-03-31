"""Test workflow with a Vapix webcam."""

from pytest_httpx import HTTPXMock

from pyvbcam.vbcam import get_vbcam


def test_is_vapix(httpx_mock: HTTPXMock):
    """Test vapix."""
    for _ in range(7):
        httpx_mock.add_response(status_code=401)
    cam = get_vbcam("KCRG-032")
    assert not cam.settings


def test_is_vapix_one_shot(httpx_mock: HTTPXMock):
    """Test vapix one shot."""
    # account for the initial failed get_settings
    for _ in range(7):
        httpx_mock.add_response(status_code=401)
    with open("tests/data/white.png", "rb") as fh:
        httpx_mock.add_response(status_code=200, content=fh.read())
    cam = get_vbcam("KCRG-032")
    assert cam.get_one_shot(res="1000x1000") is not None


def test_panDrct(httpx_mock: HTTPXMock):
    """Test vapix panDrct."""
    cam = get_vbcam("KCRG-032", settings={})
    httpx_mock.add_response(status_code=200, content=b"OK")
    assert cam.panDrct(0) is not None
