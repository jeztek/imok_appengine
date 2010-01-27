import os

try:
  import json as simplejson
except ImportError:
  import simplejson

import settings as s

from datastore import Post

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

class IncomingHandler(webapp.RequestHandler):
  def get(self):
    posts = Post.all() #.gql()

    template_data = {
      'posts' : posts,
    }
    template_path = s.template_path('incoming.html')
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(template.render(template_path, template_data))


class IncomingSmsHandler(webapp.RequestHandler):
  def get(self):
    phone = self.request.get('phone')
    message = self.request.get('message')

    self.response.headers['Content-Type'] = 'text/plain'
    if not message:
      self.response.out.write('missing message')
      return

    post = Post()
    post.message = message
    post.put()
		
    self.response.out.write(message)
    #self.response.out.write(simplejson.dumps({'hello' : 'hi'}))


def main():
  application = webapp.WSGIApplication([
    ('/incoming/', IncomingHandler),
    ('/incoming/sms/', IncomingSmsHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
