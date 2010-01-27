import os, os.path

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def template_path(template_file):
  return os.path.join(TEMPLATE_DIR, template_file)
