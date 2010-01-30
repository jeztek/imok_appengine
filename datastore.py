
from google.appengine.ext import db
try:
  from django.utils.safestring import mark_safe
except ImportError:
  def mark_safe(s):
    return s

import re, random

class ImokUser(db.Model):
  account = db.UserProperty()
  firstName = db.StringProperty(verbose_name='First name')
  lastName = db.StringProperty(verbose_name='Last name')

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
  code_time = db.DateTimeProperty()

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

  # this could maybe be a GeoPtProperty() - i don't know if it matters.
  lat      = db.FloatProperty(default=0.0)
  lon	   = db.FloatProperty(default=0.0)
  positionText = db.StringProperty(default='')
  message  = db.StringProperty()

  def asWidgetRow(self):
    meta = ''
    meta += self.datetime.strftime('%b %d %H:%M')
    if self.positionText:
      meta += ' at %s' % self.positionText
    if not (self.lat == 0 and self.lon == 0):
      meta += ' <a href="/post/%s">map</a>' % self.key()
    return mark_safe("""
<div class="widgetItem">
  <a href="/post/%s">%s</a>
  <span class="meta">%s</span>
</div>
""" % (self.key(), self.message, meta))

class SmsMessage(db.Model):
  sha_hash     = db.StringProperty(required=True)
  received     = db.DateTimeProperty()
  phone_number = db.StringProperty()
  message      = db.StringProperty()
