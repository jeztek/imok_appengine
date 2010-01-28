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

class NewUserProfileHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    user = users.get_current_user()
    username = user.nickname()
    logout_url = users.create_logout_url("/")
    profile = getProfile(True)
    form = UserProfileForm(instance=profile)
    self.render('newUserProfile.html', locals())

  def post(self):
    user = users.get_current_user()
    username = user.nickname()
    logout_url = users.create_logout_url("/")
    profile = getProfile(True)
    form = UserProfileForm(data=self.request.POST, instance=profile)
    if form.is_valid():
      # Save the data and redirect to home
      editedProfile = form.save(commit=False)
      editedProfile.put()
      defaultPhone = Phone(user=user, number=form._cleaned_data()['phone'])
      defaultPhone.put()
      self.redirect('/home')
    else:
      # Reprint the form
      self.render('newUserProfile.html', locals())

class NewUserVerifyPhoneHandler(RequestHandlerPlus):
  def get(self):
    self.render('newUserVerifyPhone.html', locals())

class NewUserContactsHandler(RequestHandlerPlus):
  def get(self):
    self.render('newUserContacts.html', locals())

def main():
  application = webapp.WSGIApplication([
    ('/newuser/profile', NewUserProfileHandler),
    ('/newuser/verifyPhone', NewUserVerifyPhoneHandler),
    ('/newuser/contacts', NewUserContactsHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
