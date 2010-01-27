from google.appengine.ext import db

import re

class ImokUser(db.Model):
  account = db.UserProperty()

class Phone(db.Model):
  """
  A registered phone number.
 
  In the DB, phone numbers are stored "+1AAABBBCCCC"
  we display them like so: AAA-BBB-CCCC
  """
  user = db.UserProperty()           # Who this number belongs to
  name = db.StringProperty()         # Nickname for the phone
  number = db.StringProperty()       # Phone number
  verified = db.BooleanProperty()    # Whether they have verified it or not
  code = db.StringProperty()         # Verification code

  @classmethod
  def is_valid_number(cls, number):
    """Is the given phone number valid?"""
    clean_number = re.sub(r'\D+', '', number)
    return (len(clean_number) == 10 or len(clean_number) == 11)

  @classmethod
  def normalize_number(cls, number):
    clean_number = re.sub(r'\D+', '', number)
    return "+%s" % clean_number

  def number_str(self):
    return re.sub(r'\+(\d{1})(\d{3})(\d{3})(\d{4})', '\g<2>-\g<3>-\g<4>', self.number)

class RegisteredEmail(db.Model):
  userName = db.UserProperty()       # Who this email belongs to
  emailAddress = db.EmailProperty()  # The email address

class Post(db.Model):
  user 	   = db.UserProperty()
  datetime = db.DateTimeProperty(auto_now_add=True)

  # this could maybe be a GeoPtProperty() - i don't know if it matters.
  lat      = db.FloatProperty()
  lon	   = db.FloatProperty()
  message  = db.StringProperty()

class SmsMessage(db.Model):
  sha_hash     = db.StringProperty(required=True)
  received     = db.DateTimeProperty()
  phone_number = db.StringProperty()
  message      = db.StringProperty()
