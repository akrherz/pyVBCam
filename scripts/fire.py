""" Fire off long term lapses for a given network """
import sys
import psycopg2.extras
import subprocess
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('settings.ini')

def run(network):
    """ Start a long term lapse for this network """
    dbconn = psycopg2.connect("host=%s user=%s dbname=%s" % (
                                            config.get('database', 'host'),
                                            config.get('database', 'user'),
                                            config.get('database', 'name')))
    cursor = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("""
    SELECT id from webcams where network = %s and online ORDER by id ASC
    """, (network,))
    for row in cursor:
        pid = subprocess.Popen("python longLapse.py %s 2" % (row[0],),
                               shell=True, 
                               stderr=subprocess.PIPE, 
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE).pid
        print "%s PID: %s" % (row[0], pid)

if __name__ == '__main__':
    # Go
    network = sys.argv[1]
    run(network)