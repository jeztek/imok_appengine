
import Cookie

from google.appengine.api import urlfetch

import logging
logging.basicConfig()
log = logging.getLogger('URLOpener')
log.setLevel(logging.DEBUG)

class ResponseWrapper(object):
  def __init__(self, response):
    self.response = response

  def content(self):
    return self.response.content
  content = property(content)

  def read(self):
    return self.response.content

  def headers(self):
    return self.response.headers
  headers = property(headers)

class URLOpener:
  def __init__(self):
    self.cookie = Cookie.SimpleCookie()
    
  def open(self, url, data=None, headers={}):
    if data is None:
      method = urlfetch.GET
    else:
      method = urlfetch.POST

    num_fetches = 1

    while url is not None:
      the_headers = self._getHeaders(self.cookie)
      the_headers.update(headers)
      
      response = urlfetch.fetch(url=url,
                                payload=data,
                                method=method,
                                headers=the_headers,
                                allow_truncated=False,
                                follow_redirects=False,
                                deadline=10
                                )

      num_fetches += 1
      data = None 
      method = urlfetch.GET
      self.cookie.load(response.headers.get('set-cookie', ''))
      url = response.headers.get('location')
    
    log.debug("Number fetches: %d" % num_fetches)
    return ResponseWrapper(response)
        
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
