
import datetime, sys

from pytz import utc, timezone

def localFromUtc(utcDt, localTz):
    utcDt = utc.localize(utcDt)
    ret = utcDt.astimezone(localTz)
    return ret
    
def formatLocalFromUtc(utcDt, localTzName):
    localTz = timezone(localTzName)
    localNow = localFromUtc(datetime.datetime.utcnow(), localTz)
    localDt = localFromUtc(utcDt, localTz)
    timeFmt = '%I:%M %p %z'
    if localDt.toordinal() == localNow.toordinal():
        # if today, say 'today'
        return 'today %s' % localDt.strftime(timeFmt)
    elif localDt.toordinal() == localNow.toordinal()-1:
        # if yesterday, say 'yesterday'
        return 'yesterday %s' % localDt.strftime(timeFmt)
    elif localDt.year == localNow.year:
        # if same year, say e.g. 'Tue Jan 01'
        return localDt.strftime('%a %b %d ' + timeFmt)
    else:
        # if different year, say e.g. '2007 Jan 01'
        return localDt.strftime('%Y %b %d ' + timeFmt)
    
