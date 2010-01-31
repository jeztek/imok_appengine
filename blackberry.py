from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

class BbHandler(webapp.RequestHandler):
  def get(self):
    self.redirect("/static/blackberry/IMOk.jad")

def main():
  application = webapp.WSGIApplication([
	('/bb', BbHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
