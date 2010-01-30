import re, random, sys

from google.appengine.api import users
from google.appengine.ext import db
import pytz
try:
  from django.utils.safestring import mark_safe
except ImportError:
  def mark_safe(s):
    return s


import re, random
from timeutils import *

TZ_CHOICES = ['America/Port-au-Prince', 'US/Pacific', 'US/Eastern'] + pytz.common_timezones

class ImokUser(db.Model):
  account = db.UserProperty()
  firstName = db.StringProperty(verbose_name='First name')
  lastName = db.StringProperty(verbose_name='Last name')
  tz = db.StringProperty(default='America/Port-au-Prince', choices=TZ_CHOICES, verbose_name='Time zone')

class Phone(db.Model):
  """
  A registered phone number.
 
  In the DB, phone numbers are stored "+1AAABBBCCCC"
  we display them like so: AAA-BBB-CCCC
  """
  user = db.UserProperty()           # Who this number belongs to
  name = db.StringProperty(default='default')         # Nickname for the phone
  number = db.StringProperty()       # Phone number
  verified = db.BooleanProperty(default=False)    # Whether they have verified it or not
  code = db.StringProperty(default='')         # Verification code

  @classmethod
  def is_valid_number(cls, number):
    """Is the given phone number valid?"""
    clean_number = re.sub(r'\D+', '', number)
    return (len(clean_number) == 10 or len(clean_number) == 11)

  @classmethod
  def normalize_number(cls, number):
    clean_number = re.sub(r'\D+', '', number)
    if len(clean_number) == 10:
      return "+1%s" % clean_number
    return "+%s" % clean_number

  @classmethod
  def generate_code(cls):
    return str(random.randrange(1111, 9999))

  def number_str(self):
    return re.sub(r'\+(\d{1})(\d{3})(\d{3})(\d{4})', '\g<2>-\g<3>-\g<4>', self.number)

class RegisteredEmail(db.Model):
  userName = db.UserProperty()       # Who this email belongs to
  emailAddress = db.EmailProperty()  # The email address

class Post(db.Model):
  user 	   = db.UserProperty()
  datetime = db.DateTimeProperty(auto_now_add=True)

  lat      = db.FloatProperty(default=0.0)
  lon	   = db.FloatProperty(default=0.0)
  positionText = db.StringProperty(default='', multiline=True)
  message  = db.StringProperty(multiline=True)
  isOk     = db.BooleanProperty(required=True, default=True)

  unique_id = db.StringProperty()
  
  @classmethod
  def gen_unique_key(cls):
#    return sha.new(str(random.randrange(1, 99999999))).hexdigest()
    return str('%016x' % random.getrandbits(64))

  hash_regex = re.compile(r'(#\S+)(?:\s?)([^#]*)(?=#?)')
  ll_regex = re.compile(r'\s*(-?\d+\.\d+),(-?\d+\.\d+)')

  @classmethod
  def getTags(cls, text):
    return Post.hash_regex.findall(text)

  def tags(self):
    return Post.getTags(self.message)

  @classmethod
  def fromText(cls, text):
    post = Post(message=text)
    tags = Post.getTags(text)

    ok = False

    atText = ''
    for tup in tags:
      if tup[0] == '#imok':
        ok = True
      if tup[0] != '#loc':
        continue
      m = ll_regex.match(tup[1])
      if m:
        post.lat = m.group(1)
        post.lon = m.group(2)
      else:
        atText += tup[1] + ' '
    post.positionText = atText
    post.isOk = ok
    return post

  def permalink(self, host=''):
    return "%s/message?unique_id=%s" % (host, self.unique_id)
      
  def asWidgetRow(self):
    meta = ''
    displayUser = users.get_current_user()
    localTzName = ImokUser.all().filter('account =', displayUser).fetch(1)[0].tz
    meta += formatLocalFromUtc(self.datetime, localTzName)
    if self.positionText:
      meta += ' at %s' % self.positionText
    if not (self.lat == 0 and self.lon == 0):
      meta += ' <a href="%s">map</a>' % self.permalink()
    return mark_safe("""
<div class="widgetItem">
  <a href="/message?unique_id=%s">%s</a>
  <span class="meta">%s</span>
</div>
""" % (self.unique_id, self.message, meta))

class SmsMessage(db.Model):
  phone_number = db.StringProperty(required=True)
  message      = db.StringProperty(required=True, multiline=True)
  direction    = db.StringProperty(required=True, 
                                   choices=set(['incoming', 'outgoing']), 
                                   default='outgoing')
  status       = db.StringProperty(required=True,
                                   choices=set(['queued', 'sent', 'delivered',
                                                'fresh', 'processed', 'unclaimed']),
                                   default="queued")
  create_time  = db.DateTimeProperty(auto_now_add=True)

