""" Reporting module """
import json

from access_log_analyzer import (
    datasource,
    get_today_ymdh, get_today_ymd,
    get_today_ym, get_today_yw, get_today_y
)

def transform_query_results(rows):
    """ Transform query results """
    dates_map = {}
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

    results = []
    for key in sorted(dates_map.keys(), reverse=True):
        results.append(dates_map[key])

    return results

def query_for_date(date_query, limit=None):
    """ Query for a given date range and convert to a report """
    return transform_query_results(datasource.query_records(date_query, limit))

def get_all_years():
    """ All years report """
    return json.dumps(query_for_date(4))

def get_all_months():
    """ All months report """
    return json.dumps(query_for_date(6))

def get_all_weeks():
    """ All weeks report """
    return json.dumps(query_for_date(7))

def get_full_report(limit=None):
    """ Full report """
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
    """ Today report """
    return json.dumps(query_for_date(8))

def get_today_hourly():
    """ Hourly report """
    return json.dumps(query_for_date(10))

def get_top_content(limit=10):
    """ Top content report """
    result = {}
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
