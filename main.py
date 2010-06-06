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
try:
  from django.utils.safestring import mark_safe
except ImportError:
  def mark_safe(s):
    return s

import settings
from datastore import *
from imokutils import *
from imokforms import *
from smsutils import *

class IntroHandler(RequestHandlerPlus):
  def get(self):
    if users.get_current_user():
      self.redirect('/home')
    else:
      mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
      login_url = users.create_login_url("/home")

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
        loggedIn = True
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        loggedIn = False
        login_url = users.create_login_url("/home")

    unique_id = self.request.get('unique_id')
    idQuery = Post.all().filter('unique_id = ', unique_id)
    post = idQuery.get()

    if not post:
      self.error(404)
      self.render('404Error.html', {})
      return

    repliesRaw = Reply.all().filter('post = ', post)
    replies = []
    
    profile = ImokUser.all().filter('account =', post.user).get()

    for reply in repliesRaw:
      replies.append({ "message": reply.message,
                       "dateTime": formatLocalFromUtc(reply.datetime, profile.tz),
                       "user": ImokUser.all().filter('account =', reply.user).get()
                       })
    

    lat = str(post.lat)
    lon = str(post.lon)
    dateTime = formatLocalFromUtc(post.datetime, profile.tz)
    key = settings.MAPS_KEY

    self.render('message.html', self.getContext(locals()))

  def post(self):
    if not users.get_current_user():
      self.redirect('/')

    loggedIn = True
    logout_url = users.create_logout_url("/")

    unique_id = self.request.get('unique_id')
    idQuery = Post.all().filter('unique_id = ', unique_id)
    post = idQuery.get()

    if not post:
      self.error(404)
      self.render('404Error.html', {})
      return

    if (not self.request.get('replyText')):
      self.error(500)
      return

    phone = Phone.all().filter('user = ', post.user).get()

    reply = Reply(message=self.request.get('replyText'),
                  post=post,
                  user=users.get_current_user())

    sendSms(phone, self.request.get('replyText'))

    db.put(reply)

    self.redirect('/message?unique_id=%s' % self.request.get('unique_id') )

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

    # profile widget
    phonesQuery = Phone.all().filter('user = ', user)
    phones = phonesQuery.fetch(1)

    # emails widget
    emailsQuery = RegisteredEmail.all().filter('userName = ', user)
    emails = emailsQuery.fetch(5)
    numEmailsNotShown = emailsQuery.count() - len(emails)

    # info widget
    sms_gateway = settings.SMS_GATEWAY

    # recent messages widget
    postsQuery = Post.all().filter('user = ', user).order('-datetime')
    posts = postsQuery.fetch(10)
    numPosts = postsQuery.count()
    numPostsNotShown = numPosts - len(posts)
    
    phone = getPhone()
    if phone and not phone.verified:
      banner = mark_safe('You must <a href="/phone/verify">verify your phone number</a> before you can post messages.')
    elif not emails:
      banner = mark_safe('You must <a href="/email">add email contacts</a> or no one will get your messages.')

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
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('blocked =', False).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    self.render('registerEmail.html', self.getContext(locals()))

  def post(self):
    if not users.get_current_user():
      self.redirect('/')
    emailString = self.request.get('emailAddress')
    emailError = getEmailErrorIfAny(emailString)
    if not emailError:
      if RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', emailString).count() > 0:
        emailError = 'Email address already registered or unsubscribed.'

    if not emailError:
      newEmail = RegisteredEmail(userName=users.get_current_user(),
                                 emailAddress=emailString,
                                 uniqueId=RegisteredEmail.gen_unique_key())
      newEmail.put()
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('blocked =', False).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    self.render('registerEmail.html', self.getContext(locals()))

class RemoveRegisteredEmailHandler(RequestHandlerPlus):
  def post(self):
    if users.get_current_user():
      removeEmail = self.request.get('emailAddress')
      removeEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', removeEmail)
      removeEmailList = removeEmailQuery.get()
      if removeEmailList:
        removeEmailList.delete()
        
    self.redirect(self.request.get('returnAddr'))

class UnsubscribeHandler(RequestHandlerPlus):
  def get(self):
    emailId = self.request.get('id', '')
    if not emailId:
      self.redirect('/')
      return

    email = RegisteredEmail.all().filter('uniqueId =', emailId).get()
    if not email:
      self.render('404Error.html', {})
      return

    user = ImokUser.all().filter('account =', email.userName).get()

    email.blocked = True
    email.put()

    self.render('unsubscribe.html', {'email': email.emailAddress, 'user': user})

def deleteUserObjects(table, user, field='user'):
  results = table.all().filter('%s = ' % field, user).fetch(1000)
  db.delete(results)

class DeleteProfileHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('deleteProfile.html', self.getContext(locals()))

  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect('/')

    deleteUserObjects(ImokUser, user, field='account')
    deleteUserObjects(Phone, user)
    deleteUserObjects(RegisteredEmail, user, field='userName')
    deleteUserObjects(Post, user)

    self.redirect(users.create_logout_url("/profile/deleted"))

class DeletedProfileHandler(RequestHandlerPlus):
  def get(self):
    self.render('deletedProfile.html', self.getContext(locals()))

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
    phone.put()

    message = "Verification Code: %s" % phone.code
    sendSms(phone, message)
    #sms = SmsMessage(phone_number=phone.number, 
    #                 message=message)
    #db.put([sms, phone])

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
    ('/unsubscribe', UnsubscribeHandler),
    ('/getInvolved', GetInvolvedHandler),

    # must be logged in for these...
    ('/email', RegisterEmailHandler),
    ('/email/remove', RemoveRegisteredEmailHandler),
    ('/phone/verify', VerifyPhoneHandler),
    ('/phone/confirm', ConfirmPhoneHandler),
    ('/profile/edit', EditProfileHandler),
    ('/profile/delete', DeleteProfileHandler),
    ('/profile/deleted', DeletedProfileHandler),
    ('/download', DownloadsHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
