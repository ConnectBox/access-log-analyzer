"""
Log ingestion related tests
"""
import unittest
from access_log_analyzer import datasource, connection_info, ingester
from access_log_analyzer.tests import (
    add_mock_log_input, clear_mock_log_input,
    set_today_ymd, set_today_ymdh
)

class TestIngestor(unittest.TestCase):
    """ setup for each test """
    def setUp(self):
        datasource.open_connection(connection_info())
        set_today_ymd('20170601')
        set_today_ymdh('2017060100')

    def tearDown(self):
        """ teardown for each test """
        datasource.close()
        clear_mock_log_input()

    def test_ingest_old_records(self):
        """ Test ingesting old records """
        self.assertTrue(datasource.connected())

        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000]'
            ' "GET /content/foo HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))
        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:23:03:23 +0000]'
            ' "GET /content/item1 HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))
        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:23:03:24 +0000]'
            ' "GET /content/item1 HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))

        ingester.ingest_log_input()

        self.assertEqual(1, datasource.query_record_count('2017', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('2017', '/content/item1'))
        self.assertEqual(1, datasource.query_record_count('201705', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('201705', '/content/item1'))
        self.assertEqual(1, datasource.query_record_count('2017W19', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('2017W19', '/content/item1'))

        # Since today is not the day that the records were created none of the
        # hourly or daily records will be inserted
        self.assertEqual(0, datasource.query_record_count('20170509', '/content/foo'))
        self.assertEqual(0, datasource.query_record_count('20170509', '/content/item1'))
        self.assertEqual(0, datasource.query_record_count('2017050923', '/content/foo'))
        self.assertEqual(0, datasource.query_record_count('2017050923', '/content/item1'))

    def test_ingest_today_records(self):
        """ Test ingesting records for today """
        self.assertTrue(datasource.connected())

        set_today_ymd('20170509')
        set_today_ymdh('2017050912')

        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:12:03:22 +0000]'
            ' "GET /content/foo HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))
        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:12:03:23 +0000]'
            ' "GET /content/item1 HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))
        add_mock_log_input((
            '8.8.8.8 - - [09/May/2017:12:03:24 +0000]'
            ' "GET /content/item1 HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'
        ))

        ingester.ingest_log_input()

        self.assertEqual(1, datasource.query_record_count('2017', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('2017', '/content/item1'))
        self.assertEqual(1, datasource.query_record_count('201705', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('201705', '/content/item1'))
        self.assertEqual(1, datasource.query_record_count('2017W19', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('2017W19', '/content/item1'))

        # Since today is the day that the records were created  the hourly and daily records
        # will be inserted
        self.assertEqual(1, datasource.query_record_count('20170509', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('20170509', '/content/item1'))
        self.assertEqual(1, datasource.query_record_count('2017050912', '/content/foo'))
        self.assertEqual(2, datasource.query_record_count('2017050912', '/content/item1'))
