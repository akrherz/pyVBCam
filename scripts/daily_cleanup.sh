#!/bin/sh
# Daily cleanup of files
# Run from ../crontab.txt

cd /mesonet/scripts/pyVBCam/tmp
rm -rf autoframes.*
