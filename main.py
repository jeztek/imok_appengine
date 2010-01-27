import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext import db
from google.appengine.api import mail


class RegisteredEmail(db.Model):
  userName = db.UserProperty()
  emailAddress = db.EmailProperty()


class MainHandler(webapp.RequestHandler):
  def get(self):

#    user = users.get_current_user()
#    username = user.nickname()
    if users.get_current_user():
        url = users.create_logout_url("/")
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        mustLogIn = "True"; # this is so the navigation bar only shows the relevant things.

    template_path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, locals()))


class RegisterEmailHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    registeredEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).order('emailAddress')
    registeredEmailList = registeredEmailQuery.fetch(100)
    
    url = users.create_logout_url("/")
    url_linktext = 'Logout'

    template_path = os.path.join(os.path.dirname(__file__), 'registerEmail.html')
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
          newEmail.put()    # this should have error correction so it doesn't go over 100.
    self.redirect('/registerEmail')


class RemoveRegisteredEmailHandler(webapp.RequestHandler):
  def post(self):
    if users.get_current_user():
      removeEmail = self.request.get('emailAddress')
      removeEmailQuery = RegisteredEmail.all().filter('userName =', users.get_current_user()).filter('emailAddress =', removeEmail)
      removeEmailList = removeEmailQuery.get()
      if removeEmailList:
        removeEmailList.delete()
        
    self.redirect('/registerEmail')


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
    self.redirect('/registerEmail')
    
    
def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/registerEmail', RegisterEmailHandler),
    ('/addRegisteredEmail', AddRegisteredEmailHandler),
    ('/removeRegisteredEmail', RemoveRegisteredEmailHandler),
    ('/spamAllRegisteredEmails', SpamAllRegisteredEmailsHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
