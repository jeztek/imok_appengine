try:
  import json
except ImportError:
  import django.utils.simplejson as json

from datastore import Post, SmsMessage, Phone, RegisteredEmail, ImokUser

from twitter import twitter_post

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

import re
import twilio

import logging

import settings as s

URL_BASE = '/%s/Accounts/%s' % (s.TWILIO_API_VERSION, s.TWILIO_ACCOUNT_ID)

SID_REGEX = re.compile(r'<Sid>([^<]*)</Sid>')
STATUS_REGEX = re.compile(r'<Status>([^<]*)</Status>')

def sendSms(sms_message):
  data = { 'From': s.SMS_GATEWAY,
           'To': sms_message.phone_number,
           'Body': sms_message.message,
           'StatusCallback': 'https://%s/smsgateway/twilio/callback' % s.HOST }
  account = twilio.Account(s.TWILIO_ACCOUNT_ID, s.TWILIO_AUTH_TOKEN)
  response = account.request(URL_BASE + '/SMS/Messages', method='POST', vars=data)

  sms_message.twilio_sid = SID_REGEX.search(response).groups()[0]
  sms_message.status = 'sent'

  sms_message.put()
  
class IncomingHandler(webapp.RequestHandler):
  def post(self):
    self.response.headers['Content-Type'] = 'text/plain'

    util = twilio.Utils(s.TWILIO_ACCOUNT_ID, s.TWILIO_AUTH_TOKEN)
    if not util.validateRequest(self.request.url, self.request.POST, self.request.headers['X-Twilio-Signature']):
      logging.error("Invalid request. Probably not Twilio.")
    
    sms_sid = self.request.get('SmsSid')
    phone = Phone.normalize_number(self.request.get('From'))
    message = self.request.get('Body')

    if not (message and phone):
      logging.error('WTF. No phone or message.')
      return

    sms_message = SmsMessage(phone_number=phone, 
                         message=message, 
                         direction='incoming',
                         twilio_sid=sms_sid,
                         status='unclaimed')
    objects = [ sms_message ]

    phone_entity = Phone.all().filter('number =', phone).get()

    if not phone_entity:
      db.put(objects)
      #self.response.out.write(json.dumps({'result': 'ok'}))
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

    twitter_post(imok_user, post.message)

    sms_message.status = 'processed'
    sms_message.put()

    response_sms = SmsMessage(phone_number=phone,
                              message="IMOk: Message received, %d contact(s) notified." % email_query.count(),
                              direction="outgoing",
                              status="queued")
    #response_sms.put()
    sendSms(response_sms)

    #self.response.out.write(message)
    #self.response.out.write(json.dumps({'result': 'ok'}))



class CallbackHandler(webapp.RequestHandler):
  def post(self):
    sms_sid = self.request.get('SmsSid', '')
    sms_status = self.request.get('SmsStatus', '')

    if sms_sid == '' or sms_status == '':
      logging.error('No SmsSid or SmsStatus!')
      return

    sms_message = SmsMessage.all().filter('twilio_sid =', sms_sid).get()
    if not sms_message:
      logging.error('No SmsMessage for the given SmsSid')
      return

    if sms_status == 'sent':
      sms_message.status = 'delivered'
    elif sms_status == 'failed':
      logging.error('SMS failed to send: %s' % sms_sid)
      sms_message.status = 'failed'
    else:
      logging.warn('Unknown status: %s' % sms_status)
      return

    sms_message.put()

def main():
  application = webapp.WSGIApplication([
    ('/smsgateway/twilio/incoming', IncomingHandler),
    ('/smsgateway/twilio/callback', CallbackHandler),
  ], debug=True)
  util.run_wsgi_app(application)

if __name__ == '__main__':
  main()
