import settings as s

from datastore import SmsMessage

class NoSuchProvider:
    pass

if s.SMS_PROVIDER == 'twilio':
    import sms_twilio as sms
elif s.SMS_PROVIDER == 'android':
    import sms_android as sms
else:
    raise NoSuchProvider

def sendSms(phone, message):
    sms_message = SmsMessage(phone_number=phone.number,
                             message=message,
                             provider=s.SMS_PROVIDER,
                             direction='outgoing',
                             status='queued')
    sms.sendSms(sms_message)
