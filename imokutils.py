
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

from datastore import ImokUser
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

class RequestHandlerPlus(webapp.RequestHandler):
  """Place to put convenience functions used by multiple request handlers."""

  def render(self, tmplName, tmplValues, contentType='text/html'):
    self.response.headers['Content-Type'] = contentType
    self.response.out.write(template.render(settings.template_path(tmplName), tmplValues))
