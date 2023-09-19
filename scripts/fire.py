""" Fire off long term lapses for a given network """

import subprocess
import sys

from pyiem.database import get_dbconnc


def go(network):
    """Fire a network"""
    dbconn, cursor = get_dbconnc("mesosite")
    cursor.execute(
        """
    SELECT id from webcams where network = %s and online ORDER by id ASC
    """,
        (network,),
    )
    for row in cursor:
        proc = subprocess.Popen(
            ["python", "long_lapse.py", row["id"], "2"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        print("%s PID: %s" % (row[0], proc.pid))
    dbconn.close()


def run(argv):
    """Start a long term lapse for this network"""
    network = argv[1]
    if network == "ALL":
        for _network in ["KCCI", "KCRG", "ISUC", "KELO", "MCFC"]:
            go(_network)
    else:
        go(network)


if __name__ == "__main__":
    # Go
    run(sys.argv)
