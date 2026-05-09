"""
Log line parsing module for access-log-analyzer.

Responsible for two things:
1. Converting nginx combined-log timestamp strings (e.g. '09/May/2025:14:23:01 +0700')
   into UTC datetime objects via the Timezone helper class.
2. Parsing a raw log line into (resource_path, [date_bucket_strings]) using
   the regex patterns loaded from config in __init__.py.

The whitelist/blacklist logic is applied here so that only relevant content
paths reach the database.  A whitelisted path is always recorded; a path that
matches only the blacklist is silently dropped.
"""
from datetime import datetime, timedelta, tzinfo
from time import strptime
import re

from access_log_analyzer import (
    TIMESTAMP_PATTERN, LOG_PATTERN,
    TIMESTAMP_GROUP, REQUEST_GROUP, REQUEST_PATTERN,
    WHITELIST_PATTERNS, BLACKLIST_PATTERNS, RESOURCE_GROUP
)

class Timezone(tzinfo):
    """Minimal tzinfo implementation for parsing nginx log timestamps.

    nginx combined-log format includes a fixed-offset timezone suffix like
    '+0700' or '-0500'.  Python's strptime does not natively handle these
    as aware datetimes, so this class wraps the offset so that
    process_request_time() can subtract it to normalise to UTC.

    Parameters
    ----------
    name : str
        Timezone offset string in the form '+HHMM' or '-HHMM', e.g. '+0700'.
    """
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
    """Convert a nginx combined-log timestamp string to a UTC datetime.

    Strips the trailing timezone offset from the string, parses the remainder
    with TIMESTAMP_PATTERN from config, then subtracts the offset to produce a
    UTC-normalised datetime.  All date buckets written to the database are in
    UTC so that multi-timezone log merges produce consistent counts.

    Parameters
    ----------
    request_time : str
        Timestamp field from the log line, e.g. '09/May/2025:14:23:01 +0700'.

    Returns
    -------
    datetime
        UTC-normalised datetime object.
    """
    date_time = strptime(request_time[:-6], TIMESTAMP_PATTERN)
    time_zone = Timezone(request_time[-5:])

    time_info = list(date_time[:6]) + [0, None]

    date = datetime(*time_info)

    return date -  timedelta(seconds=time_zone.offset.seconds)

def parse_log_line(line):
    """Parse a single nginx access log line into a (resource, date_buckets) pair.

    Applies the configured LOG_PATTERN regex to extract the timestamp and
    request fields.  Filters the request path through the whitelist then
    blacklist:
    - If it matches a WHITELIST_PATTERN it is always recorded.
    - If it matches a BLACKLIST_PATTERN (and was not whitelisted) it is dropped.

    For accepted lines, extracts the resource path and generates five date
    bucket strings covering year, month, week, day, and hour granularities.

    Parameters
    ----------
    line : str
        Raw nginx access log line.

    Returns
    -------
    [str, list[str]] or [None, None]
        On success: [resource_path, [YYYY, YYYYMM, YYYYWww, YYYYMMDD, YYYYMMDDHH]].
        On failure or filtered line: [None, None].
    """
    match = re.match(LOG_PATTERN, line)
    if not match:
        print('Failed to parse log line %s' % line)
        return [None, None]

    groups = match.groups()

    timestamp = groups[TIMESTAMP_GROUP]
    request = groups[REQUEST_GROUP]

    # Whitelist check — if any pattern matches, bypass blacklist entirely.
    whitelisted = False
    for pattern in WHITELIST_PATTERNS:
        if re.match(pattern, request):
            whitelisted = True
            break

    # Blacklist check — drop the line if it matches and was not whitelisted.
    if not whitelisted:
        for pattern in BLACKLIST_PATTERNS:
            if re.match(pattern, request):
                return [None, None]

    groups = re.match(REQUEST_PATTERN, request).groups()

    content = groups[RESOURCE_GROUP]
    timestamp = process_request_time(timestamp)

    # Build all five date-bucket strings from the normalised UTC timestamp.
    str_y = timestamp.strftime('%Y') # YYYY
    str_ym = timestamp.strftime('%Y%m') # YYYYMM
    str_yw = '%sW%s' % (str_y, '{:02d}'.format(timestamp.isocalendar()[1])) # YYYYWWW
    str_ymd = timestamp.strftime('%Y%m%d') # YYYYMMDD
    str_ymdh = timestamp.strftime('%Y%m%d%H') #YYYYMMDDHH

    return [content, [str_y, str_ym, str_yw, str_ymd, str_ymdh]]
