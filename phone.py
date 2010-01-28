import os, datetime
import logging

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

import settings as s
from datastore import *

from googlevoice import Voice
import voice_pool

class PhoneHandler(webapp.RequestHandler):
  @login_required
  def get(self, message=""):
    template_data = {
      'logout_url': users.create_logout_url('/'),
      'phones': Phone.all().filter('user = ', users.get_current_user()).fetch(100)
    }

    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(s.template_path('phone.html'), template_data))


class VerifyHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    key = self.request.get('id', '')
    if key == '':
      self.error(400)

    try:
      phone = Phone.all().filter('user =', users.get_current_user()).filter('__key__ =', db.Key(key)).get()

      template_data = {
        'logout_url': users.create_logout_url('/'),
        'phone': phone,
        'id': key
      }

      if self.request.get('message', ''):
        template_data['message'] = self.request.get('message')

      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(template.render(s.template_path('phone_verify.html'), template_data))    
    except db.BadKeyError:
      self.error(400)


class RegisterHandler(webapp.RequestHandler):
  def post(self):
    if users.get_current_user() is None:
      self.redirect('/')

    new_phone = Phone()
    new_phone.user = users.get_current_user()
    new_phone.name = self.request.get('phone_name', 'Phone')
    new_phone.verified = False

    number = self.request.get('phone_number', '')
    if not Phone.is_valid_number(number):
      template_data = {
        'logout_url': users.create_logout_url('/'),
        'phones': Phone.all().filter('user = ', users.get_current_user()).fetch(100),
        'message': "Phone number invalid.",
        'nickname': new_phone.name,
        'number': number
      }

      self.response.headers['Content-Type'] = 'text/html'
      self.response.out.write(template.render(s.template_path('phone.html'), template_data))

    else:
      new_phone.number = Phone.normalize_number(number)
      new_phone.put()
      self.redirect('/phone/')


class SendVerificationHandler(webapp.RequestHandler):
  def post(self):
    if users.get_current_user() is None:
      self.redirect('/')

    key = self.request.get('id', '')
    if key == '':
      self.error(400)
      return

    try:
      phone = Phone.all().filter('user =', users.get_current_user()).filter('__key__ =', db.Key(key)).get()

      phone.code = Phone.generate_code()
      phone.code_time = datetime.datetime.now()
      phone.put()

      v = voice_pool.get_voice()
      v.send_sms(phone.number, "Verification Code: %s" % phone.code)

    except db.BadKeyError:
      self.error(400)
      return;
      
    self.redirect('/phone/verify?id=%s' % key)    

class ConfirmVerificationHandler(webapp.RequestHandler):
  def post(self):
    if users.get_current_user() is None:
      self.redirect('/')

    key = self.request.get('id', '')
    if key == '':
      self.error(400)
      return

    code = self.request.get('code', '')

    try:
      phone = Phone.all().filter('user =', users.get_current_user()).filter('__key__ =', db.Key(key)).get()

      now = datetime.datetime.now()
      delta = now - phone.code_time
      if phone.code == code and delta.seconds < (600) and delta.seconds >= 0:
        phone.verified = True
        phone.put()
      else:
        return self.redirect('/phone/verify?id=%s&message=%s' % (key, 'Code+incorrect'))

    except db.BadKeyError:
      self.error(400)
      return;
      
    self.redirect('/phone/')    
    
def main():
  application = webapp.WSGIApplication([
    ('/phone/register', RegisterHandler),
    ('/phone/verify/send', SendVerificationHandler),
    ('/phone/verify/confirm', ConfirmVerificationHandler),
    ('/phone/verify', VerifyHandler),
    ('/phone/', PhoneHandler),
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
