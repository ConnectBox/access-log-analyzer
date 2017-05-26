from access_log_analyzer import (parser, datasource,
    log_input, get_today_ymd, get_today_ymdh)

def ingest_log_record(line, today_ymdh, today_ymd):
    content, record_dates = parser.parse_log_line(line)

    if not content:
        return

    for record_date in record_dates:
        # Skip insert of ymd since it is old
        if len(record_date) == 8 and record_date != today_ymd:
            continue
        # Skip insert of ymdh since it is old
        if len(record_date) == 10 and record_date != today_ymdh:
            continue

        # Query existing record count
        count = datasource.query_record_count(record_date, content)
        if count:
            datasource.update_record_count(count+1, record_date, content)
        else:
            datasource.insert_record_count(1, record_date, content)

def ingest_log_input():
    if not log_input:
        return

    if not datasource.connected():
        raise Error('Not connected to database')

    # Create table
    datasource.setup()

    today_ymd = get_today_ymd()
    today_ymdh = get_today_ymdh()

    # Delete daily records that are not from today
    datasource.delete_stale_records(today_ymd)
    datasource.delete_stale_records(today_ymdh)

    with log_input as log_file:
        for line in log_file:
            ingest_log_record(line, today_ymdh, today_ymd)

    datasource.commit()