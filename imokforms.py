"""Place to put field and form definitions."""

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import mail

# must import template before importing django stuff
from google.appengine.ext.db import djangoforms
try:
  from django import newforms as forms
except ImportError:
  from django import forms
import django.core.exceptions

from datastore import *
from imokutils import *

class PhoneField(forms.CharField):
  def __init__(self, *args, **kwargs):
    kwargs['max_length'] = 12
    super(PhoneField, self).__init__(*args, **kwargs)

  def clean(self, value):
    cleanNumber = re.sub(r'\D+', '', value) # ignore punctuation
    if len(cleanNumber) == 10:
      return "+1%s" % cleanNumber
    elif len(cleanNumber) == 11 and cleanNumber.startswith('1'):
      return "+%s" % cleanNumber
    else:
      raise forms.ValidationError('Please enter a valid 10-digit US phone number')

class UserProfileForm(djangoforms.ModelForm):
  phoneNumber = PhoneField(label="Phone number*")

  def saveWithPhone(self):
    editedProfile = self.save(commit=False)
    editedProfile.put()

    phone = getPhone(createIfNeeded=True)
    newNumber = self._cleaned_data()['phoneNumber']
    if newNumber != phone.number:
      phone.number = newNumber
      phone.code = ''
      phone.verified = False
      phone.put()
  
  class Meta:
    model = ImokUser
    exclude = ['account']
