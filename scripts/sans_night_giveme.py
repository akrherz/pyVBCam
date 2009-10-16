# Generate a timelapse for only images during the daytime!

import sys, os, mx.DateTime, shutil

# Change Dir to tmp
os.chdir("../tmp")
# Get the directory we wish to munge
mydir = sys.argv[1]
# Create an output folder
if not os.path.isdir(mydir+".sans"):
  os.mkdir(mydir+".sans")
# Look at what we have
os.chdir( mydir )
i = 0
j = 0
while os.path.isfile("%05i.jpg" % (i,)):
  # Figure out the timestamp
  ts = mx.DateTime.DateTime(1970,1,1) + mx.DateTime.RelativeDateTime(seconds = os.stat("%05i.jpg" % (i,))[-2]) - mx.DateTime.RelativeDateTime(hours=5)
  if (ts.hour > 6 and ts.hour < 21 and ts.strftime("%m%d") != "0706"):
    shutil.copyfile("%05i.jpg" % (i,), "../%s.sans/%05i.jpg" % (mydir, j))
    j += 1
  i += 1
