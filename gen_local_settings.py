#!/usr/bin/python

import random, os.path

if os.path.exists("local_settings.py"):
  print "File already exists. Skipping"
  exit()

random_string = str(random.randrange(111111, 999999))

f = open("local_settings.py", "w")
f.write("GATEWAY_SECRET = \"%s\"\n" % random_string)
f.close()

print "Generated."
