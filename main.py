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

import settings as s
from datastore import *

class IntroHandler(webapp.RequestHandler):
  def get(self):
    if users.get_current_user():
        logout_url = users.create_logout_url("/")
    else:
        mustLogIn = "True" # this is so the navigation bar only shows the relevant things.
        login_url = users.create_login_url("/home")
#        loginOutUrl = users.create_login_url(self.request.uri)

    template_path = s.template_path('intro.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, locals()))

class PhoneField(forms.CharField):
  def __init__(self, *args, **kwargs):
    kwargs['max_length'] = 12
    super(PhoneField, self).__init__(*args, **kwargs)

  def clean(self, value):
    cleanNumber = re.sub(r'\D+', '', value) # ignore punctuation
    if len(cleanNumber) == 10:
      return "+1%s" % cleanNumber
    elif len(cleanNumber) == 11 and cleanNumber.startswith('1'):
      return "+%s" % cleanNumber
    else:
      raise forms.ValidationError('Please enter a valid 10-digit US phone number')

class UserProfileForm(djangoforms.ModelForm):
  phone = PhoneField()
  class Meta:
    model = ImokUser
    exclude = ['account']

class RequestHandlerPlus(webapp.RequestHandler):
  def render(self, tmplName, tmplValues, contentType='text/html'):
    self.response.headers['Content-Type'] = contentType
    self.response.out.write(template.render(s.template_path(tmplName), tmplValues))

class CreateProfileHandler(RequestHandlerPlus):
  def getProfile(self):
    # Annoying that we can't use django get_or_create() idiom here.  the
    # appengine equivalent get_or_insert() seems to allow querying by
    # key only.  I also ran into problems trying to wrap this in a
    # transaction.
    user = users.get_current_user()
    profiles = ImokUser.all().filter('account =', user).fetch(1)
    if profiles:
      profile = profiles[0]
    else:
      profile = ImokUser(account=user)
    return profile

  @login_required
  def get(self):
    user = users.get_current_user()
    username = user.nickname()
    logout_url = users.create_logout_url("/")
    profile = self.getProfile()
    form = UserProfileForm(instance=profile)
    self.render('createProfile.html', locals())

  def post(self):
    user = users.get_current_user()
    username = user.nickname()
    logout_url = users.create_logout_url("/")
    profile = self.getProfile()
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
      self.render('createProfile.html', locals())

class HomeHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    logout_url = users.create_logout_url("/")

    template_path = s.template_path('main.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, locals()))

class GetInvolvedHandler(RequestHandlerPlus):
  def get(self):
    self.render('getInvolved.html', locals())

class RegisterEmailHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    
    logout_url = users.create_logout_url("/")

    template_path = s.template_path('register_email.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, locals()))


class AddRegisteredEmailHandler(webapp.RequestHandler):
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


class RemoveRegisteredEmailHandler(webapp.RequestHandler):
  def post(self):
    if users.get_current_user():
      removeEmail = self.request.get('emailAddress')
      removeEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', removeEmail)
      removeEmailList = removeEmailQuery.get()
      if removeEmailList:
        removeEmailList.delete()
        
    self.redirect('/email')


class SpamAllRegisteredEmailsHandler(webapp.RequestHandler):
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
    
class DownloadsHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    logout_url = users.create_logout_url("/")

    template_path = s.template_path('downloads.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, locals()))

    
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
