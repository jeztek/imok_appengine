import os, datetime, sys

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

class NewUserProfileHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    user = users.get_current_user()
    profile = getProfile(True)
    phone = getPhone()
    if phone:
      initial = dict(phoneNumber=phone.number_str())
    else:
      initial = None
    form = UserProfileForm(instance=profile, initial=initial)
    turnOnSelection1 = "selectedNavItem"
    self.render('newUserProfile.html', self.getContext(locals()))

  def post(self):
    user = users.get_current_user()
    profile = getProfile(True)
    form = UserProfileForm(data=self.request.POST, instance=profile)
    if form.is_valid():
      # Save the data and redirect to home
      form.saveWithPhone()
      self.redirect('/newuser/verifyPhone')
    else:
      # Reprint the form
      turnOnSelection1 = "selectedNavItem"
      self.render('newUserProfile.html', self.getContext(locals()))

class NewUserVerifyPhoneHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    turnOnSelection2 = "selectedNavItem"
    self.render('newUserVerifyPhone.html', self.getContext(locals()))

  def post(self):
    self.redirect('/newuser/contacts')

class NewUserContactsHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)

    turnOnSelection3 = "selectedNavItem"
    self.render('newUserContacts.html', self.getContext(locals()))

class NewUserDownloadHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    turnOnSelection4 = "selectedNavItem"
    self.render('newUserDownload.html', self.getContext(locals()))

def main():
  application = webapp.WSGIApplication([
    ('/newuser/profile', NewUserProfileHandler),
    ('/newuser/verifyPhone', NewUserVerifyPhoneHandler),
    ('/newuser/contacts', NewUserContactsHandler),
    ('/newuser/download', NewUserDownloadHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
