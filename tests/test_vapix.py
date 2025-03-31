"""Test workflow with a Vapix webcam."""

from pytest_httpx import HTTPXMock

from pyvbcam.vbcam import get_vbcam


def test_is_vapix(httpx_mock: HTTPXMock):
    """Test vapix."""
    for _ in range(7):
        httpx_mock.add_response(status_code=401)
    cam = get_vbcam("KCRG-002")
    assert not cam.settings
