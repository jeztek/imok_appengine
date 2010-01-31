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
try:
  from django.utils.safestring import mark_safe
except ImportError:
  def mark_safe(s):
    return s

import settings
from datastore import *
from imokutils import *
from imokforms import *

KML_STYLES = """
  <StyleMap id="msn_red-circle">
    <Pair>
      <key>normal</key>
      <styleUrl>#sn_red-circle</styleUrl>
    </Pair>
    <Pair>
      <key>highlight</key>
      <styleUrl>#sh_red-circle</styleUrl>
    </Pair>
  </StyleMap>
  <Style id="sh_red-circle">
    <IconStyle>
      <scale>1.3</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/red-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <Style id="sn_red-circle">
    <IconStyle>
      <scale>1.1</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/red-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <Style id="sn_ylw-circle">
    <IconStyle>
      <scale>1.1</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <Style id="sh_ylw-circle">
    <IconStyle>
      <scale>1.3</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <StyleMap id="msn_ylw-circle">
    <Pair>
      <key>normal</key>
      <styleUrl>#sn_ylw-circle</styleUrl>
    </Pair>
    <Pair>
      <key>highlight</key>
      <styleUrl>#sh_ylw-circle</styleUrl>
    </Pair>
  </StyleMap>
  <Style id="sh_grn-circle">
    <IconStyle>
      <scale>1.3</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <Style id="sn_grn-circle">
    <IconStyle>
      <scale>1.1</scale>
      <Icon>
        <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle.png</href>
      </Icon>
      <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
    </IconStyle>
    <ListStyle>
      <ItemIcon>
        <href>http://maps.google.com/mapfiles/kml/paddle/grn-circle-lv.png</href>
      </ItemIcon>
    </ListStyle>
  </Style>
  <StyleMap id="msn_grn-circle">
    <Pair>
      <key>normal</key>
      <styleUrl>#sn_grn-circle</styleUrl>
    </Pair>
    <Pair>
      <key>highlight</key>
      <styleUrl>#sh_grn-circle</styleUrl>
    </Pair>
  </StyleMap>
""".lstrip()

class KmlHandler(RequestHandlerPlus):
  def get(self):
    kml = """
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
""".lstrip()
    kml += KML_STYLES
    posts = Post.all().fetch(1000)
    for post in posts:
        if post.hasLocation():
            user = post.user
            profile = ImokUser.all().filter('account =', post.user).fetch(1)[0]
            dateTime = formatLocalFromUtc(post.datetime, profile.tz)
            desc = template.render(settings.template_path('messageInfo.html'), self.getContext(locals()))
            kml += """
  <Placemark>
    <name>%s</name>
    <description><![CDATA[%s]]></description>
    <styleUrl>#msn_red-circle</styleUrl>
    <Point>
      <coordinates>%f,%f,0</coordinates>
    </Point>
  </Placemark>
""" % (profile.getShortName(), desc, post.lon, post.lat)
    kml += """
</Document>
</kml>
"""
    self.writeResponse(kml, contentType='application/vnd.google-earth.kml+xml')

def main():
  application = webapp.WSGIApplication([
    ('/export/imok.kml', KmlHandler),
                                        
  ], debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()

