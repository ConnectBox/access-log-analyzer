import json

from access_log_analyzer import (datasource,
    get_today_ymdh, get_today_ymd,
    get_today_ym, get_today_yw, get_today_y)

def transform_query_results(rows):
    datesMap = {}
    for row in rows:
        date = row[0]
        resource = row[1]
        count = row[2]
        
        dateData = datesMap.get(date)
        if not dateData:
            dateData = {}
            dateData['date'] = date
            dateData['stats'] = []
            datesMap[date] = dateData

        value = {}
        value['count'] = count
        value['resource'] = resource
        dateData['stats'].append(value)

    results = []
    for key in sorted(datesMap.keys(), reverse=True):
        results.append(datesMap[key])

    return results

def query_for_date(date_query, limit=None):
    return transform_query_results(datasource.query_records(date_query, limit))

def get_all_years():
    return json.dumps(query_for_date(4))

def get_all_months():
    return json.dumps(query_for_date(6))

def get_all_weeks():
    return json.dumps(query_for_date(7))

def get_full_report(limit=None):
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
    return json.dumps(query_for_date(8))

def get_today_hourly():
    return json.dumps(query_for_date(10))

def get_top_content(limit=10):
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
