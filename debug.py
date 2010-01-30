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

class DebugHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    self.render('debug.html', self.getContext(locals()))

def deleteAll(query):
  count = query.count()
  results = query.fetch(count)
  db.delete(results)

class ResetDbHandler(RequestHandlerPlus):
  def post(self):
    if users.is_current_user_admin():
      deleteAll(ImokUser.all())
      deleteAll(Phone.all())
      deleteAll(RegisteredEmail.all())
      deleteAll(Post.all())
      self.render('resetdb.html', self.getContext(locals()))
    else:
      self.error(403)
      self.response.out.write('403 Forbidden')

class DebugPostHandler(RequestHandlerPlus):
  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect("/")

    p = Post(user=user, message='test message', lat=37., lon=-122.)
    p.unique_id = Post.gen_unique_key()
    p.put()

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

For more information, click the link below.

""" + self.request.host_url + "/message?unique_id=" + str(p.unique_id) +
"""
Please let us know if you have any questions.

The ImOK.com Team
""")
    self.redirect('/home')
    
def main():
  application = webapp.WSGIApplication([
    ('/debug', DebugHandler),
    ('/debug/resetdb', ResetDbHandler),
    ('/debug/post', DebugPostHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
