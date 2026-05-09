"""
Access Log Analyzer — package initialisation.

This module is the entry point for the package.  It runs at import time and
does three things that every other module in the package depends on:

1. Parses command-line arguments so the rest of the package can share them
   without re-parsing.
2. Merges the built-in defaults.cfg with the optional site config file and
   exposes every config value as a module-level constant.
3. Opens the log input stream (stdin or named files) unless --report-only was
   requested.

All module-level constants defined here (DATABASE_DIRECTORY, LOG_PATTERN, etc.)
are imported directly by datasource, ingester, parser, and reporting.
"""
# pylint: disable=invalid-name

import configparser
import os
import argparse
import sqlite3
import fileinput
import time
from datetime import datetime

def parse_args():
    """Parse command-line arguments for the access-log-analyzer tool.

    Defines the full CLI surface: input file(s), database name, output name,
    config file path, and a --report-only flag that skips ingestion.

    Returns
    -------
    argparse.Namespace
        Parsed argument object shared across the package.
    """
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

# ---------------------------------------------------------------------------
# Configuration loading
# Always read the built-in defaults first so every key is guaranteed to exist,
# then overlay the optional site config file so operators can override without
# touching the package source.
# ---------------------------------------------------------------------------
config_parser = configparser.ConfigParser()
config_parser.read_file(open('%s/defaults.cfg' % os.path.dirname(__file__)))
if args.config:
    config_parser.read([args.config])

# ---------------------------------------------------------------------------
# Module-level constants derived from merged config.
# These are imported directly by other modules in the package — changing a key
# name here requires a matching change in datasource, ingester, parser, and
# reporting.
# ---------------------------------------------------------------------------

# Main
DATABASE_DIRECTORY = config_parser.get('main', 'DATABASE_DIRECTORY')
OUTPUT_DIRECTORY = config_parser.get('main', 'OUTPUT_DIRECTORY')

# Parser — regex patterns and capture-group indices for nginx combined log format
LOG_PATTERN = config_parser.get('parser', 'LOG_PATTERN')
TIMESTAMP_GROUP = int(config_parser.get('parser', 'TIMESTAMP_GROUP'))
REQUEST_PATTERN = config_parser.get('parser', 'REQUEST_PATTERN')
REQUEST_GROUP = int(config_parser.get('parser', 'REQUEST_GROUP'))
RESOURCE_GROUP = int(config_parser.get('parser', 'RESOURCE_GROUP'))
TIMESTAMP_PATTERN = config_parser.get('parser', 'TIMESTAMP_PATTERN')

# Build whitelist and blacklist from config sections.
# Whitelist takes priority: a whitelisted path is always recorded even if it
# also matches a blacklist pattern.  Blacklisted paths are silently dropped.
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
    """Return the filesystem path to the SQLite database file.

    Combines DATABASE_DIRECTORY from config with the db name derived from
    --db-name (defaults to 'access_log').  Used by datasource.open_connection().

    Returns
    -------
    str
        Absolute path to the .db file, e.g. '/var/lib/access-log-analyzer/access_log.db'
    """
    return '%s/%s' % (DATABASE_DIRECTORY, dbname)

# ---------------------------------------------------------------------------
# Log input stream — opened here so the file handle is shared across the
# package rather than reopened per module.  Set to None when --report-only is
# requested so ingester.ingest_log_input() exits immediately without reading.
# ---------------------------------------------------------------------------
log_input = None
if not args.report_only:
    log_input = fileinput.input(files=args.inputfile)

def get_today_ymdh():
    """Return the current UTC hour as a 10-char string YYYYMMDDHH.

    Used as the key for per-hour access records in the SQLite database.
    Records keyed by YMDH that don't match today's value are dropped during
    ingestion to keep the per-hour table current-day only.
    """
    return time.strftime('%Y%m%d%H')

def get_today_ymd():
    """Return the current UTC date as an 8-char string YYYYMMDD.

    Used as the key for per-day access records.  Records older than today's
    YYYYMMDD are dropped during ingestion.
    """
    return time.strftime('%Y%m%d')

def get_today_ym():
    """Return the current UTC year-month as a 6-char string YYYYMM.

    Used as the key for per-month access records in reporting queries.
    """
    return time.strftime('%Y%m')

def get_today_yw():
    """Return the current UTC year and ISO week number as YYYYWWW.

    Format is '<YYYY>W<week>' where week is zero-padded to two digits, e.g.
    '2025W03'.  Used as the key for per-week access records.
    """
    return '%sW%s' % (time.strftime('%Y'), time.strftime('%V'))

def get_today_y():
    """Return the current UTC year as a 4-char string YYYY.

    Used as the key for per-year access records in reporting queries.
    """
    return time.strftime('%Y')
