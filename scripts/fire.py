""" Fire off long term lapses for a given network """
from __future__ import print_function

import subprocess
import sys

import psycopg2.extras
import pyvbcam.utils as camutils


def go(network):
    """Fire a network"""
    dbconn = camutils.get_dbconn()
    cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        """
    SELECT id from webcams where network = %s and online ORDER by id ASC
    """,
        (network,),
    )
    for row in cursor:
        proc = subprocess.Popen(
            "python long_lapse.py %s 2" % (row[0],),
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
        )
        print("%s PID: %s" % (row[0], proc.pid))


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
