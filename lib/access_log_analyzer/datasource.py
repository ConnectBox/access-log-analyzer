"""
SQLite database access module for access-log-analyzer.

Uses a module-level STATE dict instead of a class so callers can import
individual functions without instantiating an object.  The dict stores the
active sqlite3 connection and cursor between calls, acting as a lightweight
connection pool with exactly one slot.

The single table 'records' stores (record_date, resource, record_count) rows
where record_date is a variable-length string whose length encodes the
granularity: 4=year, 6=month, 7=week (YYYYWww), 8=day, 10=hour.  All
reporting and ingestion queries exploit this length convention to select the
correct time-bucket rows.
"""
import sqlite3

# Module-level connection state.  A dict is used so functions can mutate it
# without needing a global declaration for each key.
STATE = {}
STATE['connected'] = False

def connected():
    """Return True if the database connection is currently open.

    Other modules check this before performing operations so they can raise a
    meaningful error rather than hitting a KeyError on STATE['cursor'].
    """
    return STATE['connected']

def open_connection(conn_info):
    """Open a SQLite connection to the database at conn_info and store it in STATE.

    Parameters
    ----------
    conn_info : str
        Filesystem path to the .db file, as returned by __init__.connection_info().

    Side-effects
    ------------
    Populates STATE['conn'], STATE['cursor'], and sets STATE['connected'] = True.
    """
    STATE['conn'] = sqlite3.connect(conn_info)
    STATE['cursor'] = STATE['conn'].cursor()
    STATE['connected'] = True

def setup():
    """Create the records table and its unique index if they do not already exist.

    The unique index on (record_date, resource) enforces that each
    (time-bucket, path) pair has exactly one row.  Ingestion uses
    UPDATE rather than INSERT when the row already exists.  Called once per
    run by ingester.ingest_log_input() before any rows are written.
    """
    cursor = STATE['cursor']
    cursor.execute((
        'CREATE TABLE  IF NOT EXISTS'
        ' records (record_date varchar(10), resource varchar(256), record_count int)'))
    cursor.execute((
        'CREATE UNIQUE INDEX IF NOT EXISTS'
        ' date_content ON records (record_date, resource)'))

def commit():
    """Flush all pending writes to the SQLite database file.

    Called once at the end of ingestion after all log lines have been
    processed.  Not called after every row because SQLite batch commits are
    dramatically faster than per-row commits.
    """
    STATE['conn'].commit()

def close():
    """Close the database connection and clear STATE.

    Deletes conn and cursor from STATE and resets connected to False so
    subsequent calls to connected() return False and callers know to
    re-open before operating.
    """
    STATE['conn'].close()
    del STATE['conn']
    del STATE['cursor']
    STATE['connected'] = False

def delete_stale_records(period):
    """Delete all records whose date bucket matches period's length but not its value.

    The record_date column encodes time granularity by string length (4=year,
    6=month, 7=week, 8=day, 10=hour).  For any given period string (e.g. today's
    YYYYMMDD), rows of the same length that don't match today are stale — they
    represent a previous day's per-day counts — and should be removed so only
    the current period accumulates.

    Parameters
    ----------
    period : str
        Today's date string in one of the supported formats (e.g. '20250509').
    """
    STATE['cursor'].execute((
        'DELETE FROM records'
        ' WHERE length(record_date) = ? AND record_date != ?'), [len(period), period])

def query_records(date_query, limit=None):
    """Query content access records, grouped and sorted by date and count.

    Two calling modes depending on the type of date_query:

    - int: selects all rows whose record_date has exactly date_query characters,
      i.e. all records at a given granularity (e.g. 8 = all days, 6 = all months).
    - str: selects rows whose record_date exactly equals date_query, i.e. a
      single time bucket (e.g. '20250509' = one specific day).

    Results are ordered by date descending then count descending so callers get
    most-recent, most-popular content first.

    Parameters
    ----------
    date_query : int or str
        Granularity length (int) or exact date string (str).
    limit : int, optional
        Maximum rows to return.  None means no limit.

    Returns
    -------
    sqlite3.Cursor
        Cursor over (record_date, resource, sum(record_count)) rows.
    """
    limit_clause = ''
    if limit:
        limit_clause = ' LIMIT %d' % limit

    # Integer query: match all rows whose date string is the given length,
    # summing counts so multiple ingestion runs don't double-count.
    if isinstance(date_query, int):
        return STATE['cursor'].execute(
            ("SELECT record_date, resource, sum(record_count)"
             "FROM records WHERE length(record_date) = ? "
             "GROUP BY record_date, resource "
             "ORDER BY record_date DESC, record_count DESC, resource%s") % limit_clause,
            [date_query])

    # String query: match an exact date bucket value.
    return STATE['cursor'].execute(
        ("SELECT record_date, resource, sum(record_count)"
         "FROM records WHERE record_date = ? "
         "GROUP BY record_date, resource "
         "ORDER BY record_date DESC, record_count DESC, resource%s") % limit_clause,
        [date_query])

def query_record_count(record_date, resource):
    """Return the current access count for a specific (date, resource) pair.

    Used by the ingester to decide whether to INSERT a new row or UPDATE an
    existing one.  Returns 0 when no row exists so the caller can treat both
    cases uniformly with count+1.

    Parameters
    ----------
    record_date : str
        The date bucket string (e.g. '20250509').
    resource : str
        The URL path of the content item.

    Returns
    -------
    int
        Current count, or 0 if the row does not exist.
    """
    cursor = STATE['cursor']
    cursor.execute((
        'SELECT record_count FROM records'
        ' WHERE record_date = ? AND resource = ?'), [record_date, resource])
    row = cursor.fetchone()
    if row is not None:
        return row[0]
    return 0

def update_record_count(count, record_date, resource):
    """Update the access count for an existing (date, resource) row.

    Called by the ingester when query_record_count() returned a non-zero value,
    meaning the row already exists and only needs its counter incremented.

    Parameters
    ----------
    count : int
        New count value (previous count + 1).
    record_date : str
        The date bucket string.
    resource : str
        The URL path of the content item.
    """
    STATE['cursor'].execute((
        'UPDATE records SET record_count = ?'
        ' WHERE record_date = ? AND resource =?'), [count, record_date, resource])

def insert_record_count(count, record_date, resource):
    """Insert a new (date, resource, count) row into the records table.

    Called by the ingester when query_record_count() returned 0, meaning this
    is the first access to this resource in this time bucket.

    Parameters
    ----------
    count : int
        Initial count (always 1 for a first-seen record).
    record_date : str
        The date bucket string.
    resource : str
        The URL path of the content item.
    """
    STATE['cursor'].execute('INSERT INTO records VALUES (?,?,?)', [record_date, resource, count])
