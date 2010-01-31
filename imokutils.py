import sys

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
import django.core.validators # can't import django before appengine

from datastore import ImokUser, Phone
import settings

def getProfile(createIfNeeded=False):
  # Annoying that we can't use django get_or_create() idiom here.  the
  # appengine equivalent get_or_insert() seems to allow querying by
  # key only.  I also ran into problems trying to wrap this in a
  # transaction.
  user = users.get_current_user()
  profiles = ImokUser.all().filter('account =', user).fetch(1)
  if profiles:
    profile = profiles[0]
  else:
    if createIfNeeded:
      profile = ImokUser(account=user)
    else:
      profile = None
  return profile

def getPhone(createIfNeeded=False):
  user = users.get_current_user()
  phones = (Phone.all()
            .filter('user = ', user)
            .fetch(1))
  if phones:
    phone = phones[0]
  else:
    if createIfNeeded:
      phone = Phone(user=user)
    else:
      phone = None
  return phone

class RequestHandlerPlus(webapp.RequestHandler):
  """Place to put convenience functions used by multiple request handlers."""

  def getContext(self, localVars):
      context = dict(user = users.get_current_user(),
                     logout_url = users.create_logout_url("/"))
      context.update(localVars)
      return context

  def render(self, tmplName, tmplValues, contentType='text/html'):
    self.writeResponse(template.render(settings.template_path(tmplName), tmplValues))

  def writeResponse(self, text, contentType='text/html'):
    self.response.headers['Content-Type'] = contentType
    self.response.out.write(text)

def getEmailErrorIfAny(email):
  try:
    django.core.validators.isValidEmail(email, None)
  except django.core.validators.ValidationError, exc:
    return 'Enter a valid e-mail address'
  else:
    return None
