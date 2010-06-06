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

import re
import twilio
import personFinder
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
    phoneNumber = Phone.normalize_number(self.request.get('From'))
    text = self.request.get('Body')

    if not (text and phoneNumber):
      logging.error('WTF. No phoneNumber or message text.')
      return

    smsMessage = SmsMessage(phone_number=phoneNumber, 
                            message=text, 
                            direction='incoming',
                            twilio_sid=sms_sid,
                            status='unclaimed')

    phone_entity = Phone.all().filter('number =', phoneNumber).get()

    if not phone_entity:
      db.put([smsMessage])
      #self.response.out.write(json.dumps({'result': 'ok'}))
      return

    user = phone_entity.user
    self.savePostAndPush(text, phoneNumber, user, smsMessage)

  def savePostAndPush(self, text, phoneNumber, user, smsMessage=None, bogusTimestamp=None):
    post = Post.fromText(text)
    if bogusTimestamp != None:
      post.datetime = bogusTimestamp
    post.unique_id = Post.gen_unique_key()
    post.user = user
    objects = [post]
    if smsMessage != None:
      smsMessage.status = 'queued'
      objects.append(smsMessage)
    db.put(objects)

    ######################################################################
    # send email

    # FIX: this block of code does not belong in sms_twilio

    imok_user = ImokUser.getProfileForUser(user)
    email_query = RegisteredEmail.all().filter('userName =', user).order('emailAddress')

    debugOutput = []
    for email in email_query:
      template_data = {
        'message': post.message,
        'link': post.permalink(self.request.host_url),
        'unsubscribe_link': email.permalink(self.request.host_url),
        'user': imok_user
        }
      body = template.render(s.template_path('email.txt'), template_data)
      debugOutput.append(body)
      mail.send_mail(sender=s.MAILER_EMAIL,
                     to=email.emailAddress,
                     subject="IMOk status",
                     body=body)

    ######################################################################
    # post to person finder
    debugText = personFinder.postToPersonFinder(post)
    debugOutput.append(debugText)

    ######################################################################
    # send confirmation SMS
    if smsMessage != None:
      smsMessage.status = 'processed'
      smsMessage.put()

      response_sms = SmsMessage(phone_number=phoneNumber,
                                message="I'm OK: Message received, %d contact(s) notified." % email_query.count(),
                                direction="outgoing",
                                status="queued")
      #response_sms.put()
      sendSms(response_sms)

    #self.response.out.write(message)
    #self.response.out.write(json.dumps({'result': 'ok'}))
    return debugOutput

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
