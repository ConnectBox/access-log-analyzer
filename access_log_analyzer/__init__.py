""" Main Module """
# pylint: disable=invalid-name

import configparser
import os
import argparse
import sqlite3
import fileinput
from datetime import datetime

def parse_args():
    """ parse command line arguments """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('inputfile', nargs='?')
    arg_parser.add_argument(
        '--db-name',
        help='optional name to use for database file. default: access_log',
        default='access_log')
    arg_parser.add_argument(
        '--output-name',
        help='optional name to use for output file',
        default='stats')
    arg_parser.add_argument(
        '--config',
        help='optional configuration file',
        default='/etc/access-log-analyzer/config.cfg')
    arg_parser.add_argument(
        '--report-only',
        action='store_true',
        help='skips log ingestion and generates report from existing data')

    return arg_parser.parse_args()

args = parse_args()

config_parser = configparser.ConfigParser()
config_parser.read_file(open('%s/defaults.cfg' % os.path.dirname(__file__)))
if args.config:
    config_parser.read([args.config])

# Main
DATABASE_DIRECTORY = config_parser.get('main', 'DATABASE_DIRECTORY')
OUTPUT_DIRECTORY = config_parser.get('main', 'OUTPUT_DIRECTORY')

# Parser
LOG_PATTERN = config_parser.get('parser', 'LOG_PATTERN')
TIMESTAMP_GROUP = int(config_parser.get('parser', 'TIMESTAMP_GROUP'))
REQUEST_PATTERN = config_parser.get('parser', 'REQUEST_PATTERN')
REQUEST_GROUP = int(config_parser.get('parser', 'REQUEST_GROUP'))
RESOURCE_GROUP = int(config_parser.get('parser', 'RESOURCE_GROUP'))
TIMESTAMP_PATTERN = config_parser.get('parser', 'TIMESTAMP_PATTERN')

WHITELIST_PATTERNS = []
path_items = config_parser.items('content_whitelist_patterns')
for key, path in path_items:
    WHITELIST_PATTERNS.append(path)

BLACKLIST_PATTERNS = []
path_items = config_parser.items('content_blacklist_patterns')
for key, path in path_items:
    BLACKLIST_PATTERNS.append(path)

# Derive the database name from the log file if one is not specified
dbname = '%s.db' % args.db_name
outputname = args.output_name

def connection_info():
    """ get db connection info string """
    return '%s/%s' % (DATABASE_DIRECTORY, dbname)

log_input = None
if not args.report_only:
    log_input = fileinput.input()

def get_current_date_strings():
    """ get current date string components """
    current_time = datetime.now()
    week = current_time.isocalendar()[1]
    month = '{:02d}'.format(current_time.month)
    day = '{:02d}'.format(current_time.day)
    hour = '{:02d}'.format(current_time.hour)
    year = current_time.isocalendar()[0]
    return [str(year), month, day, hour, str(week)]

now = get_current_date_strings()

def get_today_ymdh():
    """ get current year + month + day + hour """
    return  '%s%s%s%s' % (now[0], now[1], now[2], now[3])

def get_today_ymd():
    """ get current year + month + day """
    return '%s%s%s' % (now[0], now[1], now[2])

def get_today_ym():
    """ get current year + month """
    return '%s%s' % (now[0], now[1])

def get_today_yw():
    """ get current year + week """
    return '%sW%s' % (now[0], now[4])

def get_today_y():
    """ get current year """
    return '%s' % (now[0])
