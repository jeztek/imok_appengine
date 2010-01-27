from google.appengine.ext import db

class ImokUser(db.Model):
  account = db.UserProperty()

class Phone(db.Model):
  user = db.UserProperty()           # Who this number belongs to
  name = db.StringProperty()         # Nickname for the phone
  number = db.PhoneNumberProperty()  # Phone number
  verified = db.BooleanProperty()    # Whether they have verified it or not
  code = db.StringProperty()         # Verification code

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
