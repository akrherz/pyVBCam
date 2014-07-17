#!/bin/sh
# Daily cleanup of files and orphaned codes
# Run from ../crontab.txt
# Sometimes the do_auto_lapse hangs, is this true anymore?
killall do_auto_lapse.py >& /dev/null
sleep 5
cd /mesonet/scripts/pyVBCam/tmp
rm -rf autoframes.*