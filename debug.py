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
from sms_twilio import IncomingHandler

class DebugHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('debug.html', self.getContext(locals()))

def deleteAll(table):
  query = table.all()
  count = query.count()
  results = query.fetch(count)
  db.delete(results)

class ResetDbHandler(RequestHandlerPlus):
  def post(self):
    deleteAll(ImokUser)
    deleteAll(Phone)
    deleteAll(RegisteredEmail)
    deleteAll(Post)
    deleteAll(SmsMessage)
    self.render('resetdb.html', self.getContext(locals()))

class DebugPostHandler(RequestHandlerPlus):
  def post(self):
    user = users.get_current_user()
    okUser = ImokUser.getProfileForUser(user)
    # get arbitrary phone number for this user
    phoneNumber = Phone.all().filter('user =', user).fetch(1)[0].number
    hnd = IncomingHandler()
    hnd.initialize(self.request, self.response)
    debugOutput = hnd.savePostAndPush(text='test message #loc 37,-122',
                                      phoneNumber=phoneNumber,
                                      user=user)

    self.response.headers['Content-Type'] = 'text/plain'
    if debugOutput:
      self.response.out.write("\n\n".join(debugOutput))
    else:
      self.response.out.write("no emails registered")
    
def main():
  application = webapp.WSGIApplication([
    ('/debug', DebugHandler),
    ('/debug/resetdb', ResetDbHandler),
    ('/debug/post', DebugPostHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
