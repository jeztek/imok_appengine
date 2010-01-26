from google.appengine.ext import db


class ImokUser(db.Model):
  account = db.UserProperty()

class Post(db.Model):
  user 	   = db.UserProperty()
  datetime = db.DateTimeProperty(auto_now_add=True)

  lat      = db.FloatProperty()
  lon	   = db.FloatProperty()
  message  = db.StringProperty()

class SmsMessage(db.Model):
  sha_hash     = db.StringProperty(required=True)
  received     = db.DateTimeProperty()
  phone_number = db.StringProperty()
  message      = db.StringProperty()
