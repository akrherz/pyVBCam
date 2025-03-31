"""Hello"""

import os
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyvbcam")
    pkgdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if not pkgdir.endswith("site-packages"):
        __version__ += "-dev"
except PackageNotFoundError:
    # package is not installed
    __version__ = "dev"


@dataclass
class WebCamConfig:
    """Encapsulates the configuration for a webcam."""

    cid: str
    fqdn: str = None
    ip: str = "127.0.0.1"
    lat: float = 0.0
    lon: float = 0.0
    name: str = ""
    pan0: int = 0
    password: str = ""
    port: int = 80
    res: str = "640x480"
    scrape_url: str = None
    username: str = ""
