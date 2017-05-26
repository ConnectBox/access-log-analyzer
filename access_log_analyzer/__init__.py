import configparser, os
import argparse
import sqlite3
import fileinput
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile', nargs='?')
    parser.add_argument(
        '--db-name',
        help='optional name to use for database file. default: access_log',
        default='access_log')
    parser.add_argument(
        '--output-name',
        help='optional name to use for output file',
        default='stats')
    parser.add_argument(
        '--config',
        help='optional configuration file',
        default='/etc/access-log-analyzer/config.cfg')
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='skips log ingestion and generates report from existing data')

    return parser.parse_args()

class Config(object):
    def __init__(self, configPath=None):
        parser = configparser.ConfigParser()
        parser.read_file(open('%s/defaults.cfg' % os.path.dirname(__file__)))
        if configPath:
            parser.read([configPath])

        # Main
        self.DATABASE_DIRECTORY = parser.get('main', 'DATABASE_DIRECTORY')
        self.OUTPUT_DIRECTORY= parser.get('main', 'OUTPUT_DIRECTORY')

        # Parser
        self.LOG_PATTERN = parser.get('parser', 'LOG_PATTERN')
        self.TIMESTAMP_GROUP = int(parser.get('parser', 'TIMESTAMP_GROUP'))
        self.REQUEST_PATTERN = parser.get('parser', 'REQUEST_PATTERN')
        self.REQUEST_GROUP = int(parser.get('parser', 'REQUEST_GROUP'))
        self.RESOURCE_GROUP = int(parser.get('parser', 'RESOURCE_GROUP'))
        self.TIMESTAMP_PATTERN= parser.get('parser', 'TIMESTAMP_PATTERN')

        self.WHITELIST_PATTERNS = []
        path_items = parser.items( 'content_whitelist_patterns' )
        for key, path in path_items:
            self.WHITELIST_PATTERNS.append(path)

        self.BLACKLIST_PATTERNS = []
        path_items = parser.items('content_blacklist_patterns')
        for key, path in path_items:
            self.BLACKLIST_PATTERNS.append(path)

args = parse_args()
config = Config(args.config)

# Derive the database name from the log file if one is not specified
dbname = '%s.db' % args.db_name
outputname = args.output_name

def connection_info():
    return '%s/%s' % (config.DATABASE_DIRECTORY, dbname)

log_input = None
if not args.report_only:
    log_input = fileinput.input()

def get_current_date_strings():
    current_time = datetime.now()
    week = current_time.isocalendar()[1]
    month = '{:02d}'.format(current_time.month)
    day = '{:02d}'.format(current_time.day)
    hour = '{:02d}'.format(current_time.hour)
    year = current_time.isocalendar()[0]
    return [str(year), month, day, hour, str(week)]

now = get_current_date_strings()

def get_today_ymdh():
    return  '%s%s%s%s' % (now[0], now[1], now[2], now[3])

def get_today_ymd():
    return '%s%s%s' % (now[0], now[1], now[2])

def get_today_ym():
    return '%s%s' % (now[0], now[1])

def get_today_yw():
    return '%sW%s' % (now[0], now[4])

def get_today_y():
    return '%s' % (now[0])
