import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

# must import template before importing django stuff
import django.core.validators
from google.appengine.ext.db import djangoforms
try:
  from django import newforms as forms
except ImportError:
  from django import forms
import django.core.exceptions
try:
  from django.utils.safestring import mark_safe
except ImportError:
  def mark_safe(s):
    return s

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

class AboutHandler(RequestHandlerPlus):
  def get(self):
    if users.get_current_user():
        logout_url = users.create_logout_url("/")
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        login_url = users.create_login_url("/home")

    self.render('about.html', self.getContext(locals()))

class MessageHandler(RequestHandlerPlus):
  def get(self):
    if users.get_current_user():
        logout_url = users.create_logout_url("/")
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        login_url = users.create_login_url("/home")

    unique_id = self.request.get('unique_id')
    idQuery = Post.all().filter('unique_id = ', unique_id)
    idMessage = idQuery.get()
    lat = str(idMessage.lat)
    lon = str(idMessage.lon)
    dateTime = str(idMessage.datetime)
    user = ImokUser.all().filter('account = ', idMessage.user).get()

    self.render('message.html', self.getContext(locals()))

class EditProfileHandler(RequestHandlerPlus):
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
    self.render('editProfile.html', self.getContext(locals()))

  def post(self):
    user = users.get_current_user()
    profile = getProfile(True)
    form = UserProfileForm(data=self.request.POST, instance=profile)
    if form.is_valid():
      phoneChanged = form.saveWithPhone()
      if phoneChanged:
        self.redirect('/phone/verify')
      else:
        self.redirect('/home')
    else:
      # Reprint the form
      self.render('editProfile.html', self.getContext(locals()))

class HomeHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    user = users.get_current_user()
    profile = getProfile()
    if not profile:
        self.redirect('/newuser/profile')

    phone = getPhone()
    if phone and not phone.verified:
      banner = mark_safe('You must <a href="/phone/verify">finish verifying your phone number</a> before you can post messages.')

    # profile widget
    phonesQuery = Phone.all().filter('user = ', user)
    phones = phonesQuery.fetch(1)

    # emails widget
    emailsQuery = RegisteredEmail.all().filter('userName = ', user)
    emails = emailsQuery.fetch(5)
    numEmailsNotShown = emailsQuery.count() - len(emails)

    # recent messages widget
    postsQuery = Post.all().filter('user = ', user).order('-datetime')
    posts = postsQuery.fetch(10)
    numPosts = postsQuery.count()
    numPostsNotShown = numPosts - len(posts)
    
    self.render('home.html', self.getContext(locals()))

class GetInvolvedHandler(RequestHandlerPlus):
  def get(self):
    if users.get_current_user():
        logout_url = users.create_logout_url("/")
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        login_url = users.create_login_url("/home")

    self.render('getInvolved.html', self.getContext(locals()))

class RegisterEmailHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    self.render('register_email.html', self.getContext(locals()))

  def post(self):
    if users.get_current_user():
      newEmail = RegisteredEmail()
      newEmail.userName = users.get_current_user()
      success = True
      tempEmailString = self.request.get('emailAddress')
      newEmail.emailAddress = tempEmailString
      try:
        django.core.validators.isValidEmail(tempEmailString, None)
      except django.core.validators.ValidationError:
        addError = 'Please enter a valid e-mail address.'
      else:
        newEmail.put()
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    self.render('register_email.html', self.getContext(locals()))

class RemoveRegisteredEmailHandler(RequestHandlerPlus):
  def post(self):
    if users.get_current_user():
      removeEmail = self.request.get('emailAddress')
      removeEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', removeEmail)
      removeEmailList = removeEmailQuery.get()
      if removeEmailList:
        removeEmailList.delete()
        
    self.redirect(self.request.get('returnAddr'))


class DownloadsHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('download.html', self.getContext(locals()))
    
class VerifyPhoneHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    phone = getPhone()
    if not phone:
      self.redirect('/home')
      return

    self.render('verifyPhone.html', self.getContext(locals()))

  def post(self):
    if not users.get_current_user():
      self.redirect('/')
      return

    redir_location = self.request.get('continue', '/home')

    phone = getPhone()
    if not phone:
      self.redirect(redir_location)
      return

    # Generate a code
    phone.code = Phone.generate_code()
    message = "Verification Code: %s" % phone.code
    sms = SmsMessage(phone_number=phone.number, 
                     message=message)
    db.put([sms, phone])

    self.redirect(redir_location)

class ConfirmPhoneHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    phone = getPhone()
    if not phone:
      self.redirect('/home')
      return

    self.render('confirmPhone.html', self.getContext(locals()))

  def post(self):
    if not users.get_current_user():
      self.redirect('/')
      return

    phone = getPhone()
    if not phone:
      self.redirect('/home')
      return

    errorlist = []
    code = self.request.get('code', '')
    if not code:
      errorlist.append('Must enter a code')
    elif len(code) != 4:
      errorlist.append('Code is only 4 digits')
    elif code != phone.code:
      errorlist.append('Incorrect code')

    if errorlist:
      self.render('confirmPhone.html', self.getContext(locals()))
      return

    phone.code = ''
    phone.verified = True
    phone.put()

    self.redirect('/home')


def main():
  application = webapp.WSGIApplication([
    ('/', IntroHandler),
    ('/home', HomeHandler),
    ('/about', AboutHandler),
    ('/message', MessageHandler),
    ('/getInvolved', GetInvolvedHandler),

    # must be logged in for these...
    ('/email', RegisterEmailHandler),
    #('/email/add', AddRegisteredEmailHandler),
    ('/email/remove', RemoveRegisteredEmailHandler),
    ('/phone/verify', VerifyPhoneHandler),
    ('/phone/confirm', ConfirmPhoneHandler),
    ('/profile/edit', EditProfileHandler),
    ('/download', DownloadsHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
