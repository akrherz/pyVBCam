"""Test pyvbcam.webcam module."""

import pytest

from pyvbcam import webcam


@pytest.mark.parametrize("database", ["mesosite"])
def test_webcam(dbcursor):
    """Test webcam class."""
    dbcursor.execute(
        "select *, st_x(geom) as lon, st_y(geom) as lat from webcams "
        "where id = 'KCCI-027'"
    )
    row = dbcursor.fetchone()
    with pytest.raises(NotImplementedError):
        webcam.BasicWebcam("KCCI-027", row, "user", "password")
