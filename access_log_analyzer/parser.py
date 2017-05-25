from datetime import datetime, timedelta, tzinfo
from time import strptime
import re

from access_log_analyzer import config

class Timezone(tzinfo):
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
    date_time = strptime(request_time[:-6], config.TIMESTAMP_PATTERN)
    time_zone = Timezone(request_time[-5:])

    time_info = list(date_time[:6]) + [ 0, None ]
    
    dt = datetime(*time_info) 

    return dt -  timedelta(seconds = time_zone.offset.seconds)

def parse_log_line(line):
    groups = re.match(config.LOG_PATTERN, line).groups()

    timestamp = groups[config.TIMESTAMP_GROUP]
    request = groups[config.REQUEST_GROUP]

    whitelisted = False
    for pattern in config.WHITELIST_PATTERNS:
        if re.match(pattern, request):
            whitelisted = True
            break

    if not whitelisted:
        for pattern in config.BLACKLIST_PATTERNS:
            if re.match(pattern, request):
                return [None, None]

    groups = re.match(config.REQUEST_PATTERN, request).groups()

    content = groups[config.RESOURCE_GROUP]
    timestamp = process_request_time(timestamp)

    y = timestamp.strftime('%Y') # YYYY
    ym = timestamp.strftime('%Y%m') # YYYYMM
    yw = '%sW%s' % (y, '{:02d}'.format(timestamp.isocalendar()[1])) # YYYYWWW
    ymd = timestamp.strftime('%Y%m%d') # YYYYMMDD
    ymdh = timestamp.strftime('%Y%m%d%H') #YYYYMMDDHH

    return [content, [y, ym, yw, ymd, ymdh]]