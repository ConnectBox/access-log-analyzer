""" Parsing module """
from datetime import datetime, timedelta, tzinfo
from time import strptime
import re

from access_log_analyzer import (
    TIMESTAMP_PATTERN, LOG_PATTERN,
    TIMESTAMP_GROUP, REQUEST_GROUP, REQUEST_PATTERN,
    WHITELIST_PATTERNS, BLACKLIST_PATTERNS, RESOURCE_GROUP
)

class Timezone(tzinfo):
    """ Timezone class """
    def __init__(self, name="+0000"):
        self.name = name
        seconds = int(name[:-2])*3600 + int(name[-2:])*60
        self.offset = timedelta(seconds=seconds)

    def utcoffset(self, dt):
        return self.offset

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return self.name

def process_request_time(request_time):
    """ Process request time """
    date_time = strptime(request_time[:-6], TIMESTAMP_PATTERN)
    time_zone = Timezone(request_time[-5:])

    time_info = list(date_time[:6]) + [0, None]

    date = datetime(*time_info)

    return date -  timedelta(seconds=time_zone.offset.seconds)

def parse_log_line(line):
    """ Parse access log line """
    match = re.match(LOG_PATTERN, line)
    if not match:
        print('Failed to parse log line %s' % line)
        return [None, None]

    groups = match.groups()

    timestamp = groups[TIMESTAMP_GROUP]
    request = groups[REQUEST_GROUP]

    whitelisted = False
    for pattern in WHITELIST_PATTERNS:
        if re.match(pattern, request):
            whitelisted = True
            break

    if not whitelisted:
        for pattern in BLACKLIST_PATTERNS:
            if re.match(pattern, request):
                return [None, None]

    groups = re.match(REQUEST_PATTERN, request).groups()

    content = groups[RESOURCE_GROUP]
    timestamp = process_request_time(timestamp)

    str_y = timestamp.strftime('%Y') # YYYY
    str_ym = timestamp.strftime('%Y%m') # YYYYMM
    str_yw = '%sW%s' % (str_y, '{:02d}'.format(timestamp.isocalendar()[1])) # YYYYWWW
    str_ymd = timestamp.strftime('%Y%m%d') # YYYYMMDD
    str_ymdh = timestamp.strftime('%Y%m%d%H') #YYYYMMDDHH

    return [content, [str_y, str_ym, str_yw, str_ymd, str_ymdh]]
