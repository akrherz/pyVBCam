#!/usr/bin/env python

import os, glob, sys

os.chdir("../tmp")
files = glob.glob("*%s*" % (sys.argv[1],))
for dir in files:
  print dir
  fn = (dir.split(".", 1)[1]).split("_")[:2]
  os.system("/home/ldm/bin/pqinsert -p 'lapse c 000000000000 KCCI/%s.qt BOGUS qt' %s/out.mov" % ("_".join(fn), dir) )
