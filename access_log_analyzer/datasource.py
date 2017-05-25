import sqlite3

__m = {}
__m['connected'] = False

def connected():
    return __m['connected']

def open(conn_info):
    __m['conn'] = sqlite3.connect(conn_info)
    __m['cursor'] = __m['conn'].cursor()
    __m['connected'] = True

def setup():
    c = __m['cursor']
    c.execute('''CREATE TABLE  IF NOT EXISTS records (record_date varchar(10), resource varchar(256), record_count int)''')
    c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS date_content ON records (record_date, resource)''')

def commit():
    __m['conn'].commit()

def close():
    __m['conn'].close()
    del __m['conn']
    del __m['cursor']
    __m['connected'] = False

def delete_stale_records(period):
    __m['cursor'].execute('DELETE FROM records WHERE length(record_date) = ? AND record_date != ?', [len(period), period])

def query_records(date_query, limit=None):
    limitClause = ''
    if limit:
        limitClause = ' LIMIT %d' % limit

    if type(date_query) == int:
        return __m['cursor'].execute(
            ("SELECT record_date, resource, sum(record_count)" 
             "FROM records WHERE length(record_date) = ? "
             "GROUP BY record_date, resource "
             "ORDER BY record_date DESC, record_count DESC, resource%s") % limitClause,
            [date_query])
    else:
        return __m['cursor'].execute(
            ("SELECT record_date, resource, sum(record_count)" 
             "FROM records WHERE record_date = ? "
             "GROUP BY record_date, resource "
             "ORDER BY record_date DESC, record_count DESC, resource%s") % limitClause,
            [date_query])

def query_record_count(record_date, resource):
    c = __m['cursor']
    c.execute('SELECT record_count FROM records WHERE record_date = ? AND resource = ?', [record_date, resource])
    row = c.fetchone()
    if row is not None:
        return row[0]
    else:
        return 0

def update_record_count(count, record_date, resource):
    __m['cursor'].execute('UPDATE records SET record_count = ? WHERE record_date = ? AND resource =?', [count , record_date, resource])

def insert_record_count(count, record_date, resource):
    __m['cursor'].execute('INSERT INTO records VALUES (?,?,?)', [record_date, resource, count])