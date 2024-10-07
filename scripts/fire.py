"""Fire off long term lapses for a given network"""

import subprocess
import sys

from pyiem.util import logger

from pyvbcam.utils import get_camids

LOG = logger()


def main(argv):
    """Go Main."""
    for camid in get_camids(argv[1]):
        proc = subprocess.Popen(
            ["python", "long_lapse.py", camid, "2"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        LOG.warning("%s PID: %s", camid, proc.pid)


if __name__ == "__main__":
    # Go
    main(sys.argv)
