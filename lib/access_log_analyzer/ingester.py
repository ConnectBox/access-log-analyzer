"""
Log ingestion module for access-log-analyzer.

Reads nginx access log lines one at a time, parses each line into a (content,
date-buckets) pair, then upserts the access count for every time granularity
(year, month, week, day, hour) into the SQLite database.

The key design constraint is that per-day and per-hour buckets are kept
current-day only: records for older YYYYMMDD or YYYYMMDDHH keys are deleted at
the start of each run.  Yearly, monthly, and weekly rows accumulate without
pruning so historical trend reports remain available.
"""
from access_log_analyzer import (
    parser, datasource,
    log_input, get_today_ymd, get_today_ymdh
)

def ingest_log_record(line, today_ymdh, today_ymd):
    """Parse and store a single nginx access log line.

    Delegates line parsing to parser.parse_log_line(), which returns the
    resource path and a list of date-bucket strings at every granularity
    (year, month, week, day, hour).  For day and hour buckets only the current
    period is kept — historical values are silently skipped to avoid inflating
    counts when old log files are replayed.

    For each bucket that passes the staleness check, the existing count is
    fetched and incremented (UPDATE) or a new row is created (INSERT).

    Parameters
    ----------
    line : str
        Raw nginx access log line.
    today_ymdh : str
        Current hour as YYYYMMDDHH; hour records not matching this are skipped.
    today_ymd : str
        Current date as YYYYMMDD; day records not matching this are skipped.
    """
    content, record_dates = parser.parse_log_line(line)

    if not content:
        return

    # Walk each time granularity returned by the parser.  Year/month/week
    # buckets (lengths 4, 6, 7) are always stored.  Day (8) and hour (10) are
    # only stored when they match today, preventing old log replays from
    # polluting the current-day stats.
    for record_date in record_dates:
        # Skip insert of ymd since it is old
        if len(record_date) == 8 and record_date != today_ymd:
            continue
        # Skip insert of ymdh since it is old
        if len(record_date) == 10 and record_date != today_ymdh:
            continue

        # Upsert: increment an existing row or create a new one with count 1.
        count = datasource.query_record_count(record_date, content)
        if count:
            datasource.update_record_count(count+1, record_date, content)
        else:
            datasource.insert_record_count(1, record_date, content)

def ingest_log_input():
    """Read all log input and persist access counts to the database.

    Entry point called by the main script after opening the database.
    Guards against being called with no input (--report-only mode) or before
    the database connection is established.

    Processing sequence:
    1. Ensure the records table exists (idempotent CREATE IF NOT EXISTS).
    2. Delete stale per-day and per-hour rows so only today's counts remain.
    3. Iterate every line of log_input, calling ingest_log_record() for each.
    4. Commit all changes in a single transaction for performance.
    """
    if not log_input:
        return

    if not datasource.connected():
        raise Error('Not connected to database')

    # Ensure table and index exist before any reads or writes.
    datasource.setup()

    today_ymd = get_today_ymd()
    today_ymdh = get_today_ymdh()

    # Prune current-day buckets that belong to previous days/hours so
    # replaying the same log file doesn't accumulate duplicate counts.
    datasource.delete_stale_records(today_ymd)
    datasource.delete_stale_records(today_ymdh)

    # Process each log line; invalid or blacklisted lines are silently dropped
    # inside ingest_log_record / parser.parse_log_line.
    with log_input as log_file:
        for line in log_file:
            ingest_log_record(line, today_ymdh, today_ymd)

    datasource.commit()
