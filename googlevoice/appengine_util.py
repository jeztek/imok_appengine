
import Cookie
import urllib
from google.appengine.api import urlfetch

import logging
logging.basicConfig()
log = logging.getLogger('URLOpener')
log.setLevel(logging.DEBUG)

class URLOpener:
  def __init__(self):
    self.cookie = Cookie.SimpleCookie()
    
  def open(self, url, data=None, headers={}):
    if data is None:
      method = urlfetch.GET
    else:
      method = urlfetch.POST

    while url is not None:
      the_headers = self._getHeaders(self.cookie)
      the_headers.update(headers)

      log.debug("Fetching: url=" + url + " headers=" + str(the_headers))
      
      response = urlfetch.fetch(url=url,
                                payload=data,
                                method=method,
                                headers=the_headers,
                                allow_truncated=False,
                                follow_redirects=False,
                                deadline=10
                                )

      data = None # Next request will be a get, so no need to send the data again. 
      method = urlfetch.GET
      self.cookie.load(response.headers.get('set-cookie', '')) # Load the cookies from the response
      url = response.headers.get('location')
    
    return response
        
  def _getHeaders(self, cookie):
    headers = {
      'User-Agent' : 'PyGoogleVoice/0.5',
      'Cookie' : self._makeCookieHeader(cookie)
      }
    return headers

  def _makeCookieHeader(self, cookie):
    cookie_header = ""
    for value in cookie.values():
      cookie_header += "%s=%s; " % (value.key, value.value)
    return cookie_header
