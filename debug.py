import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

# must import template before importing django stuff
from google.appengine.ext.db import djangoforms
try:
  from django import newforms as forms
except ImportError:
  from django import forms
import django.core.exceptions

import settings
from datastore import *
from imokutils import *
from imokforms import *

class DebugHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('debug.html', self.getContext(locals()))

def deleteAll(query):
  count = query.count()
  results = query.fetch(count)
  db.delete(results)

class ResetDbHandler(RequestHandlerPlus):
  def post(self):
    if users.is_current_user_admin():
      deleteAll(ImokUser.all())
      deleteAll(Phone.all())
      deleteAll(RegisteredEmail.all())
      deleteAll(Post.all())
      self.render('resetdb.html', self.getContext(locals()))
    else:
      self.error(403)
      self.response.out.write('403 Forbidden')

def main():
  application = webapp.WSGIApplication([
    ('/debug', DebugHandler),
    ('/debug/resetdb', ResetDbHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
