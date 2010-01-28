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

class NewUserProfileHandler(RequestHandlerPlus):
  def get(self):
    self.render('newUserProfile.html', locals())

class NewUserVerifyPhoneHandler(RequestHandlerPlus):
  def get(self):
    self.render('newUserVerifyPhone.html', locals())

class NewUserContactsHandler(RequestHandlerPlus):
  def get(self):
    self.render('newUserContacts.html', locals())

def main():
  application = webapp.WSGIApplication([
    ('/profile', NewUserProfileHandler),
    ('/verifyPhone', NewUserVerifyPhoneHandler),
    ('/contacts', NewUserContactsHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
