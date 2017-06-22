"""
Reporting related tests
"""
import unittest
import json
from access_log_analyzer import datasource, connection_info, ingester
from access_log_analyzer import reporting
from access_log_analyzer.tests import (
    add_mock_log_input,
    clear_mock_log_input, set_today_y, set_today_ym,
    set_today_yw, set_today_ymd, set_today_ymdh
)

LOG_SUFFIX = ' HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'

class TestReporting(unittest.TestCase):
    """ Reporting test case """

    def setUp(self):
        """ setup for each test """
        datasource.open_connection(connection_info())
        set_today_ymd('20170601')
        set_today_ymdh('2017060100')

    def tearDown(self):
        """ teardown for each test """
        datasource.close()
        clear_mock_log_input()

    def validate_simple_stats(  #pylint: disable-msg=too-many-arguments
            self, report_json, date1, date2,
            content_count1, content_count2, content1, content2):
        """ perform simple validation based on
             contrived stats """
        self.assertIsNotNone(report_json)

        report = json.loads(report_json)

        self.assertEqual(len(report), 2)
        year = report[0]
        self.assertIsNotNone(year)
        date = year.get('date')
        self.assertEqual(date, date1)
        stats = year.get('stats')
        self.assertIsNotNone(stats)
        self.assertEqual(len(stats), 2)

        self.assertEqual(2, stats[0].get('count'))
        self.assertEqual(1, stats[1].get('count'))
        self.assertEqual(content1, stats[0].get('resource'))
        self.assertEqual(content2, stats[1].get('resource'))

        year = report[1]
        self.assertIsNotNone(year)
        date = year.get('date')
        self.assertEqual(date, date2)
        stats = year.get('stats')
        self.assertIsNotNone(stats)
        self.assertEqual(len(stats), 2)

        self.assertEqual(content_count1, stats[0].get('count'))
        self.assertEqual(content_count2, stats[1].get('count'))
        self.assertEqual(content1, stats[0].get('resource'))
        self.assertEqual(content2, stats[1].get('resource'))

    def test_filter_images(self):
        """ Test blacklist filtering images """
        self.assertTrue(datasource.connected())

        for img_type in ['png', 'gif', 'jpg']:
            content = '/content/image.%s' % img_type
            add_mock_log_input(
                '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
                (content, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_icon_metadata(self):
        """ Test blacklist filter icon metadata """
        self.assertTrue(datasource.connected())

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/_icon_Music', LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/Music/_icon_Blues', LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_non_content(self):
        """ Test blacklist filter non-content requests """
        self.assertTrue(datasource.connected())

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/admin/index.html', LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_root(self):
        """ Test filter root content """
        self.assertTrue(datasource.connected())

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/', LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_content_folders(self):
        """ Test blacklist folders under content """
        self.assertTrue(datasource.connected())

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/music/', LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/books/', LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_not_filtered(self):
        """ Test non-filtered content """
        self.assertTrue(datasource.connected())

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            ('/content/readme.MD', LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertNotEqual('[]', report_json)

    def test_reporting_all_years(self):
        """ Test all years report """
        self.assertTrue(datasource.connected())

        content_root = '/content/foo1'
        content_item = '/content/item1'

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.validate_simple_stats(report_json, '2017', '2016', 2, 1, content_item, content_root)

    def test_reporting_all_months(self):
        """ Test all months report """
        self.assertTrue(datasource.connected())

        content_root = '/content/foo1'
        content_item = '/content/item1'

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_months()

        self.validate_simple_stats(
            report_json, '201705', '201605', 2, 1, content_item, content_root)

    def test_reporting_all_weeks(self):
        """ Test all weeks report """
        self.assertTrue(datasource.connected())

        content_root = '/content/foo1'
        content_item = '/content/item1'

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_all_weeks()

        self.validate_simple_stats(
            report_json, '2017W19', '2016W19', 2, 1, content_item, content_root)

    def test_get_full_report(self):
        """ Test full report """
        self.assertTrue(datasource.connected())

        content_root = '/content/foo1'
        content_item = '/content/item1'

        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s%s' %
            (content_root, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))
        add_mock_log_input(
            '8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s%s' %
            (content_item, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_full_report()

        self.assertIsNotNone(report_json)

        report = json.loads(report_json)

        self.validate_simple_stats(
            json.dumps(report['year']), '2017', '2016', 2, 1, content_item, content_root)
        self.validate_simple_stats(
            json.dumps(report['month']), '201705', '201605', 2, 1, content_item, content_root)
        self.validate_simple_stats(
            json.dumps(report['week']), '2017W19', '2016W19', 2, 1, content_item, content_root)

    def test_top_content(self): #pylint: disable=R0914, R0915
        """ Test top content report """
        set_today_y('2017')
        set_today_yw('2017W20')
        set_today_ym('201705')
        set_today_ymd('20170517')
        set_today_ymdh('2017051723')

        self.assertTrue(datasource.connected())

        access_log_template = '8.8.8.8 - - [%s +0000] "GET %s%s'

        first_content_for_year = '/content/01year'
        second_content_for_year = '/content/02year'
        first_year_count = 300
        second_year_count = 200
        for _ in range(0, first_year_count):
            add_mock_log_input(
                access_log_template % ('01/Apr/2017:23:03:23', first_content_for_year, LOG_SUFFIX))
        for _ in range(0, second_year_count):
            add_mock_log_input(
                access_log_template % ('01/Apr/2017:23:03:23', second_content_for_year, LOG_SUFFIX))

        first_content_for_month = '/content/01month'
        second_content_for_month = '/content/02month'
        first_month_count = 50
        second_month_count = 25
        for _ in range(0, first_month_count):
            add_mock_log_input(
                access_log_template % ('01/May/2017:23:03:23', first_content_for_month, LOG_SUFFIX))
        for _ in range(0, second_month_count):
            add_mock_log_input(
                access_log_template % (
                    '02/May/2017:23:03:23', second_content_for_month, LOG_SUFFIX))

        first_content_for_week = '/content/01week'
        second_content_for_week = '/content/02week'
        first_week_count = 20
        second_week_count = 11
        for _ in range(0, first_week_count):
            add_mock_log_input(
                access_log_template % ('15/May/2017:23:03:23', first_content_for_week, LOG_SUFFIX))
        for _ in range(0, second_week_count):
            add_mock_log_input(
                access_log_template % ('16/May/2017:23:03:23', second_content_for_week, LOG_SUFFIX))

        first_content_for_day = '/content/01day'
        second_content_for_day = '/content/02day'
        first_day_count = 10
        second_day_count = 5
        for _ in range(0, first_day_count):
            add_mock_log_input(
                access_log_template % ('17/May/2017:11:03:23', first_content_for_day, LOG_SUFFIX))
        for _ in range(0, second_day_count):
            add_mock_log_input(
                access_log_template % ('17/May/2017:12:03:23', second_content_for_day, LOG_SUFFIX))

        first_content_for_hour = '/content/01hour'
        second_content_for_hour = '/content/02hour'
        first_hour_count = 2
        second_hour_count = 1
        for _ in range(0, first_hour_count):
            add_mock_log_input(
                access_log_template % ('17/May/2017:23:03:23', first_content_for_hour, LOG_SUFFIX))
        for _ in range(0, second_hour_count):
            add_mock_log_input(
                access_log_template % ('17/May/2017:23:10:23', second_content_for_hour, LOG_SUFFIX))

        ingester.ingest_log_input()

        report_json = reporting.get_top_content(2)

        self.assertIsNotNone(report_json)

        report = json.loads(report_json)

        top_year = report.get('year')
        self.assertIsNotNone(top_year)
        self.assertEqual(len(top_year), 2)
        self.assertEqual(top_year[0]['resource'], first_content_for_year)
        self.assertEqual(top_year[0]['count'], first_year_count)
        self.assertEqual(top_year[1]['resource'], second_content_for_year)
        self.assertEqual(top_year[1]['count'], second_year_count)

        top_month = report.get('month')
        self.assertIsNotNone(top_month)
        self.assertEqual(len(top_month), 2)
        self.assertEqual(top_month[0]['resource'], first_content_for_month)
        self.assertEqual(top_month[0]['count'], first_month_count)
        self.assertEqual(top_month[1]['resource'], second_content_for_month)
        self.assertEqual(top_month[1]['count'], second_month_count)

        top_week = report.get('week')
        self.assertIsNotNone(top_week)
        self.assertEqual(len(top_week), 2)
        self.assertEqual(top_week[0]['resource'], first_content_for_week)
        self.assertEqual(top_week[0]['count'], first_week_count)
        self.assertEqual(top_week[1]['resource'], second_content_for_week)
        self.assertEqual(top_week[1]['count'], second_week_count)

        top_day = report.get('day')
        self.assertIsNotNone(top_day)
        self.assertEqual(len(top_day), 2)
        self.assertEqual(top_day[0]['resource'], first_content_for_day)
        self.assertEqual(top_day[0]['count'], first_day_count)
        self.assertEqual(top_day[1]['resource'], second_content_for_day)
        self.assertEqual(top_day[1]['count'], second_day_count)

        top_hour = report.get('hour')
        self.assertIsNotNone(top_hour)
        self.assertEqual(len(top_hour), 2)
        self.assertEqual(top_hour[0]['resource'], first_content_for_hour)
        self.assertEqual(top_hour[0]['count'], first_hour_count)
        self.assertEqual(top_hour[1]['resource'], second_content_for_hour)
        self.assertEqual(top_hour[1]['count'], second_hour_count)
