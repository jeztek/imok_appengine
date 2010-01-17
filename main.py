import os, datetime

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

# DATABASE
class ImokUser(db.Model):
  account = db.UserProperty()
  
  
# WEBAPP
class MainHandler(webapp.RequestHandler):

  def get(self):
    template_data = {
      'username' : 'Test User',
    }

    template_path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, template_data))


class UserRegisterHandler(webapp.RequestHandler):

  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write("Hello!")

# MAIN
def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/user/register', UserRegisterHandler),
                                        
    ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
