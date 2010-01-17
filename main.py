import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util


class MainHandler(webapp.RequestHandler):

  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))

    template_data = {
      'username' : user.nickname(),
      'logout_url' : users.create_logout_url("/"),
    }

    template_path = os.path.join(os.path.dirname(__file__), 'main.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, template_data))


class UserRegisterHandler(webapp.RequestHandler):

  def get(self):
    username = self.request.get('username')
    
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write("Hello " + username)


def main():
  application = webapp.WSGIApplication([
    ('/', MainHandler),
    ('/user/register/', UserRegisterHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
