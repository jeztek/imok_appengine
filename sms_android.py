try:
  import json
except ImportError:
  import django.utils.simplejson as json

from datastore import Post, SmsMessage, Phone, RegisteredEmail, ImokUser

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

import settings as s

def sendSms(sms_message):
  sms_message.put()

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

    if not phone_entity:
      db.put(objects)
      self.response.out.write(json.dumps({'result': 'ok'}))
      return

    post = Post.fromText(message)
    post.unique_id = Post.gen_unique_key()
    post.user = phone_entity.user
    objects.append(post)
    sms_message.status = 'queued'

    db.put(objects)

    imok_user = ImokUser.all().filter('account =', phone_entity.user).get()
    email_query = RegisteredEmail.all().filter('userName =', phone_entity.user).order('emailAddress')

    for email in email_query:
      template_data = {
        'message': post.message,
        'link': post.permalink(self.request.host_url),
        'unsubscribe_link': email.permalink(self.request.host_url),
        'user': imok_user
        }
      body = template.render(s.template_path('email.txt'), template_data)
      mail.send_mail(sender=s.MAILER_EMAIL,
                     to=email.emailAddress,
                     subject="IMOk status",
                     body=body)

    sms_message.status = 'processed'

    response_sms = SmsMessage(phone_number=phone,
                              message="IMOk: Message received, %d contact(s) notified." % email_query.count(),
                              direction="outgoing",
                              status="queued")

    db.put([ response_sms, sms_message ])

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

class StatusHandler(webapp.RequestHandler):
  @login_required
  def get(self):
    user = users.get_current_user()
    if not user.is_current_user_admin():
      self.redirect('/home')
    
    

def main():
  application = webapp.WSGIApplication([
    ('/smsgateway/android/incoming', IncomingHandler),
    ('/smsgateway/android/outgoing', OutgoingHandler),
    #('/smsgateway/status', StatusHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
