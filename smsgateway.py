try:
  import json
except ImportError:
  import django.utils.simplejson as json

from datastore import Post, SmsMessage, Phone

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util

import settings as s

class IncomingHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/json'

    if self.request.get('secret', '') != s.GATEWAY_SECRET:
      self.error(403)
      self.response.out.write(json.dumps({ 'result': 'error', 'message': 'no' }))
      return

    phone = Phone.normalize_number(self.request.get('phone'))
    message = self.request.get('message')

    if not (message and phone):
      result = { 'result': 'error',
                 'message': 'missing phone and/or message' }
      self.response.out.write(json.dumps(result))
      return

    message = SmsMessage(phone_number=phone, 
                         message=message, 
                         direction='incoming',
                         status='queued')
    message.put()

    #post = Post()
    #post.message = message
    #post.put()
		
    #self.response.out.write(message)
    self.response.out.write(json.dumps({'result': 'ok'}))

class OutgoingHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/json'

    if self.request.get('secret', '') != s.GATEWAY_SECRET:
      self.error(403)
      self.response.out.write(json.dumps({ 'result': 'error', 'message': 'no' }))
      return

    # Handle any messages the phone sent
    sent_messages_str = self.request.get('messages', '[]')
    sent_messages = json.loads(sent_messages_str)

    try:
      messages = db.get(sent_messages)
      def deliver(m):
        m.status = 'delivered'
        return m
      map(deliver, messages)
      db.put(messages)
    except db.BadKeyError:
      # TODO: Do something
      pass

    # Send them any new messages
    messages = SmsMessage.all().filter('status =', 'queued').filter('direction =', 'outgoing').fetch(100)

    def modify(m):
      m.status = 'sent'
      return { 'id': str(m.key()), 'message': m.message, 'phone': m.phone_number }
    send_messages = map(modify, messages)

    db.put(messages)

    self.response.headers['Content-Type'] = 'text/json'
    self.response.out.write(json.dumps({'result': 'ok', 'messages': send_messages}))

def main():
  application = webapp.WSGIApplication([
    ('/smsgateway/incoming', IncomingHandler),
    ('/smsgateway/outgoing', OutgoingHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
