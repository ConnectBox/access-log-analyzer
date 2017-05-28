""" Main entry point """

from access_log_analyzer import (
    connection_info,
    datasource, reporting,
    ingester, outputname,
    OUTPUT_DIRECTORY
)

def main():
    """ Main method """
    datasource.open_connection(connection_info())

    ingester.ingest_log_input()

    with open('%s/%s.json' % (OUTPUT_DIRECTORY, outputname), 'w') as out:
        out.write(reporting.get_full_report())

    with open('%s/%s.top10.json' % (OUTPUT_DIRECTORY, outputname), 'w') as out:
        out.write(reporting.get_top_content())

    datasource.close()

if __name__ == '__main__':
    main()
