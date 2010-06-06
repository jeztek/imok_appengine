import os, datetime

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

# must import template before importing django stuff
import django.core.exceptions
from django.utils import simplejson

import settings
from datastore import *
from imokutils import *
from imokforms import *
from timeutils import *

class MapHandler(RequestHandlerPlus):
  @login_required
  def get(self):
    posts = [p
             for p in Post.all().order('-datetime').fetch(100)
             if p.hasLocation()]
    features = []
    now = datetime.datetime.utcnow()
    for post in posts:
        profile = ImokUser.getProfileForUser(post.user)
        phoneNumber = Phone.all().filter('user =', post.user).fetch(1)[0].number
        diff = now - post.datetime
        if post.isOk:
            color='green'
        else:
            if diff.seconds > 60*60*12:
                color = 'yellow'
            else:
                color = 'red'
        feature = dict(lat=post.lat,
                       lon=post.lon,
                       positionText=post.positionText,
                       tags=post.tags(),
                       message=post.message,
                       firstName=profile.firstName,
                       lastName=profile.lastName,
                       phoneNumber=phoneNumber,
                       timestamp=formatLocalFromUtc(post.datetime, profile.tz),
                       color=color,
                       url=post.permalink(),
                       )
        features.append(feature)
    featureText = simplejson.dumps(features)
    self.render('map.html', self.getContext(dict(features=featureText)))
    
def main():
  application = webapp.WSGIApplication([
    ('/data/map', MapHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
