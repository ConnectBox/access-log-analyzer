import sqlite3

STATE = {}
STATE['connected'] = False

def connected():
    return STATE['connected']

def open(conn_info):
    STATE['conn'] = sqlite3.connect(conn_info)
    STATE['cursor'] = STATE['conn'].cursor()
    STATE['connected'] = True

def setup():
    cursor = STATE['cursor']
    cursor.execute((
        'CREATE TABLE  IF NOT EXISTS'
        ' records (record_date varchar(10), resource varchar(256), record_count int)'))
    cursor.execute((
        'CREATE UNIQUE INDEX IF NOT EXISTS'
        ' date_content ON records (record_date, resource)'))

def commit():
    STATE['conn'].commit()

def close():
    STATE['conn'].close()
    del STATE['conn']
    del STATE['cursor']
    STATE['connected'] = False

def delete_stale_records(period):
    STATE['cursor'].execute((
        'DELETE FROM records'
        ' WHERE length(record_date) = ? AND record_date != ?'), [len(period), period])

def query_records(date_query, limit=None):
    limit_clause = ''
    if limit:
        limit_clause = ' LIMIT %d' % limit

    if type(date_query) == int:
        return STATE['cursor'].execute(
            ("SELECT record_date, resource, sum(record_count)"
             "FROM records WHERE length(record_date) = ? "
             "GROUP BY record_date, resource "
             "ORDER BY record_date DESC, record_count DESC, resource%s") % limit_clause,
            [date_query])
    else:
        return STATE['cursor'].execute(
            ("SELECT record_date, resource, sum(record_count)"
             "FROM records WHERE record_date = ? "
             "GROUP BY record_date, resource "
             "ORDER BY record_date DESC, record_count DESC, resource%s") % limit_clause,
            [date_query])

def query_record_count(record_date, resource):
    cursor = STATE['cursor']
    cursor.execute((
        'SELECT record_count FROM records'
        ' WHERE record_date = ? AND resource = ?'), [record_date, resource])
    row = cursor.fetchone()
    if row is not None:
        return row[0]
    return 0

def update_record_count(count, record_date, resource):
    STATE['cursor'].execute((
        'UPDATE records SET record_count = ?'
        ' WHERE record_date = ? AND resource =?'), [count, record_date, resource])

def insert_record_count(count, record_date, resource):
    STATE['cursor'].execute('INSERT INTO records VALUES (?,?,?)', [record_date, resource, count])
