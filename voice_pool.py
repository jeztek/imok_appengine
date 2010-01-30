
from google.appengine.api import memcache

from googlevoice import Voice

VOICE_KEY = 'voice_instance'

# Returned a logged in instance of a voice object
def get_voice():
  v = Voice()

  serialized = memcache.get(VOICE_KEY)
  if not serialized is None:
    v.from_json(serialized)
    return v

  v.login()
  memcache.set(VOICE_KEY, v.to_json())
  return v
