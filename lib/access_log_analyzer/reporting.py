"""
Reporting module for access-log-analyzer.

Converts raw SQLite rows into JSON structures consumed by the ConnectBox HAT
display service (page_stats.py) and the admin UI.

All public functions return a JSON string.  The key building block is
transform_query_results(), which reshapes a flat list of (date, resource,
count) rows into a list of {date, stats:[{resource, count}]} dicts ordered
newest-first.  The get_top_content() function uses the exact date-bucket
string (e.g. today's YYYYMM) to retrieve only the current period's top N
items at each granularity.
"""
import json

from access_log_analyzer import (
    datasource,
    get_today_ymdh, get_today_ymd,
    get_today_ym, get_today_yw, get_today_y
)

def transform_query_results(rows):
    """Reshape a flat list of DB rows into a list of per-date stat objects.

    Input rows are (record_date, resource, count) tuples as returned by
    datasource.query_records().  Output is a list of dicts, one per unique
    date, each containing a 'date' key and a 'stats' list of
    {resource, count} dicts.  Sorted newest-first by date string (which sorts
    lexicographically because all formats are zero-padded).

    Parameters
    ----------
    rows : iterable of (str, str, int)
        Raw rows from the SQLite cursor.

    Returns
    -------
    list[dict]
        [{'date': 'YYYYMMDD', 'stats': [{'resource': '/path', 'count': N}, ...]}, ...]
    """
    dates_map = {}
    # Group rows by date, building a stats list for each unique date bucket.
    for row in rows:
        date = row[0]
        resource = row[1]
        count = row[2]

        date_data = dates_map.get(date)
        if not date_data:
            date_data = {}
            date_data['date'] = date
            date_data['stats'] = []
            dates_map[date] = date_data

        value = {}
        value['count'] = count
        value['resource'] = resource
        date_data['stats'].append(value)

    # Sort keys descending so the most recent date appears first in the list.
    results = []
    for key in sorted(dates_map.keys(), reverse=True):
        results.append(dates_map[key])

    return results

def query_for_date(date_query, limit=None):
    """Query the database and return transformed results for the given date selector.

    Thin wrapper that chains datasource.query_records() with
    transform_query_results() so callers don't need to call both.

    Parameters
    ----------
    date_query : int or str
        Granularity length (int) or exact date string (str) — see datasource.query_records().
    limit : int, optional
        Cap on number of rows returned.

    Returns
    -------
    list[dict]
        Transformed result list as per transform_query_results().
    """
    return transform_query_results(datasource.query_records(date_query, limit))

def get_all_years():
    """Return a JSON report of access counts grouped by year (all years on record).

    Uses date-string length 4 (YYYY) to select all year-granularity rows.
    """
    return json.dumps(query_for_date(4))

def get_all_months():
    """Return a JSON report of access counts grouped by month (all months on record).

    Uses date-string length 6 (YYYYMM) to select all month-granularity rows.
    """
    return json.dumps(query_for_date(6))

def get_all_weeks():
    """Return a JSON report of access counts grouped by ISO week (all weeks on record).

    Uses date-string length 7 (YYYYWww) to select all week-granularity rows.
    """
    return json.dumps(query_for_date(7))

def get_full_report(limit=None):
    """Return a combined JSON report with year, month, and week breakdowns.

    Queries all three granularities and bundles them into a single dict with
    'year', 'month', and 'week' keys so the caller gets a complete overview
    in one call.

    Parameters
    ----------
    limit : int, optional
        Maximum rows per granularity bucket.

    Returns
    -------
    str
        JSON string: {'year': [...], 'month': [...], 'week': [...]}.
    """
    result = {}
    data = query_for_date(4, limit)
    if not data:
        data = []

    result['year'] = data

    data = query_for_date(6, limit)
    if not data:
        data = []
    result['month'] = data

    data = query_for_date(7, limit)
    if not data:
        data = []
    result['week'] = data

    return json.dumps(result)

def get_today():
    """Return a JSON report of per-resource access counts for today.

    Uses date-string length 8 (YYYYMMDD) to select today's day-granularity rows.
    """
    return json.dumps(query_for_date(8))

def get_today_hourly():
    """Return a JSON report of per-resource access counts for the current hour.

    Uses date-string length 10 (YYYYMMDDHH) to select the current hour's rows.
    """
    return json.dumps(query_for_date(10))

def get_top_content(limit=10):
    """Return a JSON report of the top N content items at each time granularity.

    Unlike the get_all_* functions which return historical data across all
    periods, this function queries each granularity using the *current* date
    string (e.g. today's YYYYMM) so only the active period's top items are
    returned.  This is what the HAT display service uses to show 'trending'
    content.

    Parameters
    ----------
    limit : int, optional
        Number of top items to return per granularity (default 10).

    Returns
    -------
    str
        JSON string: {'year': [...], 'month': [...], 'week': [...],
                      'day': [...], 'hour': [...]}.
        Each list contains {resource, count} dicts ordered by count descending.
    """
    result = {}

    # Query each time granularity using the current period's exact date string.
    # data[0] contains the single date bucket for the current period; .get('stats', [])
    # extracts just the resource/count list.
    data = query_for_date(get_today_y(), limit)
    if data:
        result['year'] = data[0].get('stats', [])
    else:
        result['year'] = []

    data = query_for_date(get_today_ym(), limit)
    if data:
        result['month'] = data[0].get('stats', [])
    else:
        result['month'] = []

    data = query_for_date(get_today_yw(), limit)
    if data:
        result['week'] = data[0].get('stats', [])
    else:
        result['week'] = []

    data = query_for_date(get_today_ymd(), limit)
    if data:
        result['day'] = data[0].get('stats', [])
    else:
        result['day'] = []

    data = query_for_date(get_today_ymdh(), limit)
    if data:
        result['hour'] = data[0].get('stats', [])
    else:
        result['hour'] = []
    return json.dumps(result)
