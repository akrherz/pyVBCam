"""Test pyvbcam.webcam module."""

import pytest

from pyvbcam import WebCamConfig
from pyvbcam.webcam import BasicWebcam


def test_webcam_get_settings_failure():
    """Test webcam class."""
    with pytest.raises(NotImplementedError):
        BasicWebcam(WebCamConfig(cid="KCCI-027"))
