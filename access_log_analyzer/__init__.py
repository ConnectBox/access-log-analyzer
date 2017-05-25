import configparser, os
import argparse
import sqlite3
import fileinput
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')
    parser.add_argument('--dbname', help='optional name to use for database file')
    parser.add_argument('--outputname', help='optional name to use for output file', default='stats')
    parser.add_argument('--config', help='optional configuration file', default='/etc/access-log-analyzer/config.cfg')

    return parser.parse_args()

class Config(object):
    def __init__(self, configPath=None):
        config = configparser.ConfigParser()
        config.read_file(open('%s/defaults.cfg' % os.path.dirname(__file__)))
        if configPath:
            config.read([configPath])

        # Main
        self.DATABASE_DIRECTORY= config.get('main', 'DATABASE_DIRECTORY')
        self.OUTPUT_DIRECTORY= config.get('main', 'OUTPUT_DIRECTORY')

        # Parser
        self.LOG_PATTERN = config.get('parser', 'LOG_PATTERN')
        self.TIMESTAMP_GROUP = int(config.get('parser', 'TIMESTAMP_GROUP'))
        self.REQUEST_PATTERN = config.get('parser', 'REQUEST_PATTERN')
        self.REQUEST_GROUP = int(config.get('parser', 'REQUEST_GROUP'))
        self.RESOURCE_GROUP = int(config.get('parser', 'RESOURCE_GROUP'))
        self.TIMESTAMP_PATTERN= config.get('parser', 'TIMESTAMP_PATTERN')

args = parse_args()
config = Config(args.config)

# Derive the database name from the log file if one is not specified
dbname = args.dbname
if not dbname:
    # Remove path from input file
    filename = os.path.basename(args.inputfile)

    # Strip extension from filename
    parts = os.path.splitext(filename)
    while parts[0].find('.') != -1:
        parts = os.path.splitext(parts[0])

    dbname = '%s.db' % parts[0]

def connection_info():
    return '%s/%s' % (config.DATABASE_DIRECTORY, dbname)

log_input = fileinput.input()


def get_current_date_strings():
    now = datetime.now()
    week = now.isocalendar()[1]
    month = '{:02d}'.format(now.month)
    day = '{:02d}'.format(now.day)
    hour = '{:02d}'.format(now.hour)
    year = now.isocalendar()[0]
    return [str(year), month, day, hour, str(week)]

# Todo this could be cleaned up - just need a single string and trim off the last 2 for ymd
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
