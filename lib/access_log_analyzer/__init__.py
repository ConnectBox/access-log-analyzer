""" Main Module """
# pylint: disable=invalid-name

import configparser
import os
import argparse
import sqlite3
import fileinput
import time
from datetime import datetime

def parse_args():
    """ parse command line arguments """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('inputfile', metavar='FILE', nargs='*')
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
    log_input = fileinput.input(files=args.inputfile)

def get_today_ymdh():
    """ get current year + month + day + hour """
    return time.strftime('%Y%m%d%H')

def get_today_ymd():
    """ get current year + month + day """
    return time.strftime('%Y%m%d')

def get_today_ym():
    """ get current year + month """
    return time.strftime('%Y%m')

def get_today_yw():
    """ get current year + week """
    return time.strftime('%Y%V')

def get_today_y():
    """ get current year """
    return time.strftime('%Y')
