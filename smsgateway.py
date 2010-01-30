try:
  import json
except ImportError:
  import django.utils.simplejson as json

from datastore import Post, SmsMessage, Phone, RegisteredEmail, ImokUser

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template, util
from google.appengine.api import mail

import settings as s

def secret_required(handler_method):
  def check_secret(self, *args):
    if self.request.get('secret', '') != s.GATEWAY_SECRET:
      self.error(404)
      self.response.headers['Content-Type'] = 'text/plain'
      self.response.out.write("404 - Not Found\n")
      return
    handler_method(self, *args)
  return check_secret

class IncomingHandler(webapp.RequestHandler):
  @secret_required
  def post(self):
    self.response.headers['Content-Type'] = 'text/json'

    phone = Phone.normalize_number(self.request.get('phone'))
    message = self.request.get('message')

    if not (message and phone):
      result = { 'result': 'error',
                 'message': 'missing phone and/or message' }
      self.response.out.write(json.dumps(result))
      return

    sms_message = SmsMessage(phone_number=phone, 
                         message=message, 
                         direction='incoming',
                         status='unclaimed')
    objects = [ sms_message ]

    phone_entity = Phone.all().filter('number =', phone).get()
    post = None
    if phone_entity:
      post = Post.fromText(message)
      post.unique_id = Post.gen_unique_key()
      post.user = phone_entity.user
      objects.append(post)

      sms_message.status = 'queued'
		
    db.put(objects)

    if not phone_entity:
      self.response.out.write(json.dumps({'result': 'ok'}))
      return

    imok_user = ImokUser.all().filter('account =', phone_entity.user).get()
    email_query = RegisteredEmail.all().filter('userName =', phone_entity.user).order('emailAddress')
    addresses = []
    for email in email_query:
      addresses.append(email.emailAddress)
    
    if addresses:
      template_data = {
        'message': post.message,
        'link': post.permalink(self.request.host_url),
        'user': imok_user
        }
      body = template.render(s.template_path('email.txt'), template_data)
      mail.send_mail(sender=imok_user.account.email(),
                     to=imok_user.account.email(),
                     bcc=addresses,
                     subject="I'm OK",
                     body=body)
      sms_message.status = 'processed'
      sms_message.put()
        
    #self.response.out.write(message)
    self.response.out.write(json.dumps({'result': 'ok'}))

class OutgoingHandler(webapp.RequestHandler):
  @secret_required
  def post(self):
    self.response.headers['Content-Type'] = 'text/json'

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
