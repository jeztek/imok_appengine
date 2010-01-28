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

class IntroHandler(RequestHandlerPlus):
  def get(self):
    if users.get_current_user():
        logout_url = users.create_logout_url("/")
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        login_url = users.create_login_url("/home")
        #loginOutUrl = users.create_login_url(self.request.uri)

    self.render('intro.html', self.getContext(locals()))

class CreateProfileHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    user = users.get_current_user()
    username = user.nickname()
    logout_url = users.create_logout_url("/")
    profile = getProfile(True)
    form = UserProfileForm(instance=profile)
    self.render('createProfile.html', self.getContext(locals()))

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
      self.render('createProfile.html', self.getContext(locals()))

class HomeHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    user = users.get_current_user()
    profile = getProfile()
    if not profile:
        self.redirect('/newuser/profile')
    postsQuery = Post.all().filter('user = ', user).order('-datetime')
    posts = postsQuery.fetch(10)
    isMorePosts = postsQuery.count() > 10
    logout_url = users.create_logout_url("/")

    self.render('home.html', self.getContext(locals()))

class GetInvolvedHandler(RequestHandlerPlus):
  def get(self):
    self.render('getInvolved.html', self.getContext(locals()))

class RegisterEmailHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    
    logout_url = users.create_logout_url("/")

    self.render('register_email.html', self.getContext(locals()))

class AddRegisteredEmailHandler(RequestHandlerPlus):
  def post(self):
    if users.get_current_user():
      newEmail = RegisteredEmail()
      newEmail.userName = users.get_current_user()
      success = True
      try:
        # can't not remember to validate email
        tempEmailString = self.request.get('emailAddress')
        newEmail.emailAddress = tempEmailString
        # WHY DOESN'T THIS WORK? I SUCK. do I need a real mail server for this? -OTAVIO
        if not mail.is_email_valid(tempEmailString):
          success = False
      except:
        success = False
      else:
        if success:
          newEmail.put()
    self.redirect('/email')

class RemoveRegisteredEmailHandler(RequestHandlerPlus):
  def post(self):
    if users.get_current_user():
      removeEmail = self.request.get('emailAddress')
      removeEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', removeEmail)
      removeEmailList = removeEmailQuery.get()
      if removeEmailList:
        removeEmailList.delete()
        
    self.redirect('/email')


class SpamAllRegisteredEmailsHandler(RequestHandlerPlus):
  def post(self):
    if users.get_current_user():
      registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
      addresses = []
      for registeredEmail in registeredEmailQuery:
        addresses.append(registeredEmail.emailAddress)
      
      if (len(addresses) > 0):
        mail.send_mail(sender=users.get_current_user().email(),
                      to=users.get_current_user().email(),
                      bcc=addresses,
                      subject="I'm OK",
                      body="""
Dear Registered User:

This is an auto generated email please do not reply. You are registered to receive emails
regarding the status of USER. This email lets you know they are OK.

Please let us know if you have any questions.

The ImOK.com Team
""")
    self.redirect('/email')
    
class DownloadsHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    logout_url = users.create_logout_url("/")

    self.render('downloads.html', self.getContext(locals()))
    
def main():
  application = webapp.WSGIApplication([
    ('/', IntroHandler),
    ('/home', HomeHandler),
    ('/getInvolved', GetInvolvedHandler),
    ('/email', RegisterEmailHandler),
    ('/email/add', AddRegisteredEmailHandler),
    ('/email/remove', RemoveRegisteredEmailHandler),
    ('/email/spam', SpamAllRegisteredEmailsHandler),
    ('/profile/create', CreateProfileHandler),
    ('/downloads', DownloadsHandler),
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
