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
    turnOnSelection1 = "selectedNavItem"
    self.render('newUserProfile.html', self.getContext(locals()))

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

def main():
  application = webapp.WSGIApplication([
    ('/newuser/profile', NewUserProfileHandler),
    ('/newuser/verifyPhone', NewUserVerifyPhoneHandler),
    ('/newuser/contacts', NewUserContactsHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
