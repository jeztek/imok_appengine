
from google.appengine.api import urlfetch

from datastore import ImokUser
import settings

def getPfifRecord(post):
  imokUser = ImokUser.getProfileForUser(post.user)
  if post.positionText == '':
    if post.lat == 0.0:
      posText = ''
    else:
      posText = '%.6f,%.6f' % (post.lat, post.lon)
  else:
    posText = post.positionText
  if posText == '':
    posElt = ('\n      <pfif:last_known_location>%s</pfif:last_known_location>'
              % post.positionText)
  else:
    posElt = ''
  # FIX: remove TEST_PREFIX when we start pushing to real Person Finder
  TEST_PREFIX = 'iamok_'
  args = dict(imokHost='imokapp.appspot.com',
              userId=post.user.user_id(),
              entryDate=post.datetime.isoformat() + 'Z',
              firstName=TEST_PREFIX + imokUser.firstName,
              lastName=TEST_PREFIX + imokUser.lastName,
              userName='%s%s %s%s' % (TEST_PREFIX, imokUser.firstName, TEST_PREFIX, imokUser.lastName),
              posElt=posElt,
              postId=post.unique_id,
              message=post.message,
              )
  
  # We are intentionally leaving out some PFIF fields that we
  # have info for, due to privacy concerns.  Any information we send
  # to Person Finder is totally public.
  return '''<?xml version="1.0" encoding="utf-8"?>
<pfif:pfif xmlns:pfif="http://zesty.ca/pfif/1.2"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://zesty.ca/pfif/1.2
                     http://zesty.ca/pfif/1.2/pfif-1.2.xsd">
  <pfif:person>
    <pfif:person_record_id>%(imokHost)s/%(userId)s</pfif:person_record_id>
    <pfif:entry_date>%(entryDate)s</pfif:entry_date>
    <pfif:author_name>%(userName)s</pfif:author_name>
    <pfif:source_name>%(imokHost)s</pfif:source_name>
    <pfif:source_date>%(entryDate)s</pfif:source_date>
    <pfif:source_url>http://%(imokHost)s/person/%(userId)s</pfif:source_url>
    <pfif:first_name>%(firstName)s</pfif:first_name>
    <pfif:last_name>%(lastName)s</pfif:last_name>
    <pfif:note>
      <pfif:note_record_id>%(imokHost)s/post/%(postId)s</pfif:note_record_id>
      <pfif:person_record_id>%(imokHost)s/%(userId)s</pfif:person_record_id>
      <pfif:entry_date>%(entryDate)s</pfif:entry_date>
      <pfif:author_name>%(userName)s</pfif:author_name>
      <pfif:source_date>%(entryDate)s</pfif:source_date>
      <pfif:status>believed_alive</pfif:status>
      <pfif:found>true</pfif:found>%(posElt)s
      <pfif:text>
        Full text of status SMS: %(message)s
      </pfif:text>
    </pfif:note>
  </pfif:person>
</pfif:pfif>
''' % args

def postToPersonFinder(post):
    pfif = getPfifRecord(post)
    url = settings.PERSON_FINDER_URL % {'key': settings.PERSON_FINDER_AUTH_KEY}
    debugOutput = pfif + '\n'
    try:
        debugOutput += '[sending request to %s]\n' % url
        response = urlfetch.fetch(url=url,
                                  payload=pfif,
                                  method='POST',
                                  deadline=settings.PERSON_FINDER_DEADLINE_SECONDS)
    except urlfetch.DownloadError:
        debugOutput += '[request timed out]\n'
    else:
        debugOutput += '[request returned with http status code %d]\n' % response.status_code
        debugOutput += 'content: %s\n' % response.content
        debugOutput += 'headers: %s\n' % response.headers

    return debugOutput
