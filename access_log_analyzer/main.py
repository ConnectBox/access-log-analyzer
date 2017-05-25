from access_log_analyzer import connection_info, datasource, reporting, ingester

def main():
    datasource.open(connection_info())

    ingester.ingest_log_input()

    print(reporting.get_all_years())

    datasource.close()

if __name__ == '__main__':
    main()