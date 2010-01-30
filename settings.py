import os, os.path

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

MAPS_KEY = 'ABQIAAAAAFc3F2oO92IOeSdh20OvwRTIaxK6J1v0NBsI6tB269QU6Hg_LRSrbrOnRs7NAA_zH6sTW8fJ-5NpgQ'

def template_path(template_file):
  return os.path.join(TEMPLATE_DIR, template_file)

try:
  from local_settings import *
except ImportError:
  pass
