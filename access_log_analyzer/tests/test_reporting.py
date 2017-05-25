import unittest
import json
from access_log_analyzer import datasource, connection_info, ingester
from access_log_analyzer import reporting
from access_log_analyzer.tests import (add_mock_log_input, 
    clear_mock_log_input, set_today_y, set_today_ym,
    set_today_yw, set_today_ymd, set_today_ymdh)

class TestReporting(unittest.TestCase):
    def setUp(self):
        datasource.open(connection_info())
        set_today_ymd('20170601')
        set_today_ymdh('2017060100')

    def tearDown(self):
        datasource.close()
        clear_mock_log_input()

    def validate_simple_stats(self, report_json, date1, date2, content_count1, content_count2, content1, content2):
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
        self.assertTrue(datasource.connected())

        for img_type in ['png', 'gif', 'jpg']:
            content = '/content/image.%s' % img_type
            add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % content)

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_icon_metadata(self):
        self.assertTrue(datasource.connected())

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % '/content/_icon_Music')
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % '/content/Music/_icon_Blues')

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_non_content(self):
        self.assertTrue(datasource.connected())

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % '/admin/index.html')

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_filter_root(self):
        self.assertTrue(datasource.connected())

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % '/content/')

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertEqual('[]', report_json)

    def test_not_filtered(self):
        self.assertTrue(datasource.connected())

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % '/content/readme.MD')

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.assertNotEqual('[]', report_json)

    def test_reporting_all_years(self):
        self.assertTrue(datasource.connected())

        contentRoot = '/content/foo1'
        contentItem = '/content/item1'

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)

        ingester.ingest_log_input()

        report_json = reporting.get_all_years()

        self.validate_simple_stats(report_json, '2017', '2016', 2, 1, contentItem, contentRoot)

    def test_reporting_all_months(self):
        self.assertTrue(datasource.connected())

        contentRoot = '/content/foo1'
        contentItem = '/content/item1'

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)

        ingester.ingest_log_input()

        report_json = reporting.get_all_months()

        self.validate_simple_stats(report_json,  '201705', '201605', 2, 1, contentItem, contentRoot)

    def test_reporting_all_weeks(self):
        self.assertTrue(datasource.connected())

        contentRoot = '/content/foo1'
        contentItem = '/content/item1'

        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2017:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:22 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentRoot)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:23 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)
        add_mock_log_input('8.8.8.8 - - [09/May/2016:23:03:24 +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"' % contentItem)

        ingester.ingest_log_input()

        report_json = reporting.get_all_weeks()

        self.validate_simple_stats(report_json,  '2017W19', '2016W19', 2, 1, contentItem, contentRoot)

    def test_top_content(self):
        set_today_y('2017')
        set_today_yw('2017W20')
        set_today_ym('201705')
        set_today_ymd('20170517')
        set_today_ymdh('2017051723')

        self.assertTrue(datasource.connected())

        access_log_template = '8.8.8.8 - - [%s +0000] "GET %s HTTP/1.1" 200 954 "http://connectbox.local/" "Mozilla/5.0"'

        firstContentForYear = '/content/01year'
        secondContentForYear = '/content/02year'
        firstYearCount = 300
        secondYearCount = 200
        for i in range(0, firstYearCount):
            add_mock_log_input(access_log_template % ('01/Apr/2017:23:03:23', firstContentForYear))
        for i in range(0, secondYearCount):
            add_mock_log_input(access_log_template % ('01/Apr/2017:23:03:23', secondContentForYear))

        firstContentForMonth = '/content/01month'
        secondContentForMonth = '/content/02month'
        firstMonthCount = 50
        secondMonthCount = 25
        for i in range(0, firstMonthCount):
            add_mock_log_input(access_log_template % ('01/May/2017:23:03:23', firstContentForMonth))
        for i in range(0, secondMonthCount):
            add_mock_log_input(access_log_template % ('02/May/2017:23:03:23', secondContentForMonth))

        firstContentForWeek = '/content/01week'
        secondContentForWeek = '/content/02week'
        firstWeekCount = 20
        secondWeekCount = 11
        for i in range(0, firstWeekCount):
            add_mock_log_input(access_log_template % ('15/May/2017:23:03:23', firstContentForWeek))
        for i in range(0, secondWeekCount):
            add_mock_log_input(access_log_template % ('16/May/2017:23:03:23', secondContentForWeek))

        firstContentForDay = '/content/01day'
        secondContentForDay = '/content/02day'
        firstDayCount = 10
        secondDayCount = 5
        for i in range(0, firstDayCount):
            add_mock_log_input(access_log_template % ('17/May/2017:11:03:23', firstContentForDay))
        for i in range(0, secondDayCount):
            add_mock_log_input(access_log_template % ('17/May/2017:12:03:23', secondContentForDay))

        firstContentForHour = '/content/01hour'
        secondContentForHour = '/content/02hour'
        firstHourCount = 2
        secondHourCount = 1
        for i in range(0, firstHourCount):
            add_mock_log_input(access_log_template % ('17/May/2017:23:03:23', firstContentForHour))
        for i in range(0, secondHourCount):
            add_mock_log_input(access_log_template % ('17/May/2017:23:10:23', secondContentForHour))

        ingester.ingest_log_input()

        report_json = reporting.get_top_content(2)

        self.assertIsNotNone(report_json)

        report = json.loads(report_json)
        
        top_year = report.get('year')
        self.assertIsNotNone(top_year)
        self.assertEqual(len(top_year), 2)
        self.assertEqual(top_year[0]['resource'], firstContentForYear)
        self.assertEqual(top_year[0]['count'], firstYearCount)
        self.assertEqual(top_year[1]['resource'], secondContentForYear)
        self.assertEqual(top_year[1]['count'], secondYearCount)

        top_month = report.get('month')
        self.assertIsNotNone(top_month)
        self.assertEqual(len(top_month), 2)
        self.assertEqual(top_month[0]['resource'], firstContentForMonth)
        self.assertEqual(top_month[0]['count'], firstMonthCount)
        self.assertEqual(top_month[1]['resource'], secondContentForMonth)
        self.assertEqual(top_month[1]['count'], secondMonthCount)

        top_week = report.get('week')
        self.assertIsNotNone(top_week)
        self.assertEqual(len(top_week), 2)
        self.assertEqual(top_week[0]['resource'], firstContentForWeek)
        self.assertEqual(top_week[0]['count'], firstWeekCount)
        self.assertEqual(top_week[1]['resource'], secondContentForWeek)
        self.assertEqual(top_week[1]['count'], secondWeekCount)

        top_day = report.get('day')
        self.assertIsNotNone(top_day)
        self.assertEqual(len(top_day), 2)
        self.assertEqual(top_day[0]['resource'], firstContentForDay)
        self.assertEqual(top_day[0]['count'], firstDayCount)
        self.assertEqual(top_day[1]['resource'], secondContentForDay)
        self.assertEqual(top_day[1]['count'], secondDayCount)

        top_hour = report.get('hour')
        self.assertIsNotNone(top_hour)
        self.assertEqual(len(top_hour), 2)
        self.assertEqual(top_hour[0]['resource'], firstContentForHour)
        self.assertEqual(top_hour[0]['count'], firstHourCount)
        self.assertEqual(top_hour[1]['resource'], secondContentForHour)
        self.assertEqual(top_hour[1]['count'], secondHourCount)