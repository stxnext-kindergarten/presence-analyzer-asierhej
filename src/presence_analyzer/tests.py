# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals
import os.path
import json
import datetime
import unittest

import main  # pylint: disable=relative-import
import utils  # pylint: disable=relative-import
import views  # pylint: disable=unused-import, relative-import

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_XML_DATA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'export_test.xml'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update(
            {
                'XML_DATA': TEST_XML_DATA,
                'DATA_CSV': TEST_DATA_CSV
            }
        )
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page render template.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(
            data[0],
            {
                'user_id': 36,
                'name': 'Anna W.',
                'avatar': 'https://intranet.stxnext.pl:443/api/images/users/36'
            }
        )

    def test_presenc_weekday_view(self):
        """
        Test mean presence time of given user grouped by weekday.
        """
        resp = self.client.get('/api/v1/presence_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Weekday', 'Presence (s)'],
                ['Mon', 24123],
                ['Tue', 16564],
                ['Wed', 25321],
                ['Thu', 45968],
                ['Fri', 6426],
                ['Sat', 0],
                ['Sun', 0]
            ]
        )

    def test_mean_time_weekday_view(self):
        """
        Test of mean presence time grouped by weekday of given user.
        """
        resp = self.client.get('/api/v1/mean_time_weekday/11')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Mon', 24123.0],
                ['Tue', 16564.0],
                ['Wed', 25321.0],
                ['Thu', 22984.0],
                ['Fri', 6426.0],
                ['Sat', 0.0],
                ['Sun', 0.0]
            ]
        )

    def test_presence_start_end(self):
        """
        Test the medium time to come to the office and medium time of leave.
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                ['Mon', 0, 0],
                ['Tue', 34745.0, 64792.0],
                ['Wed', 33592.0, 58057.0],
                ['Thu', 38926.0, 62631.0],
                ['Fri', 0, 0],
                ['Sat', 0, 0],
                ['Sun', 0, 0]
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update(
            {
                'XML_DATA': TEST_XML_DATA,
                'DATA_CSV': TEST_DATA_CSV
            }
        )

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_seconds_since_midnight(self):
        """
        Test calculation of secounds since midnight.
        """
        data = utils.seconds_since_midnight(datetime.time(2, 42, 23))
        self.assertEqual(data, 9743)
        data = utils.seconds_since_midnight(datetime.time(00, 00, 00))
        self.assertEqual(data, 0)

    def test_interval(self):
        """
        Test calculation of seconds between the time the objects.
        """
        start_example = datetime.time(13, 59, 59)
        end_example = datetime.time(23, 59, 59)
        data = utils.interval(start_example, end_example)
        self.assertEqual(36000, data)
        data = utils.interval(end_example, start_example)
        self.assertEqual(-36000, data)

    def test_mean(self):
        """
        Test of mean and if empty list returns 0.
        """
        data = utils.mean([100, 100, 100])
        self.assertEqual(100, data)
        data = utils.mean([0.5, 0.2, 0.3, 234])
        self.assertEqual(58.75, data)
        data = utils.mean([])
        self.assertEqual(0, data)

    def test_day_start_end(self):
        """
        Test start and end work times sorted by weekday.

        """
        user = utils.get_data()
        data = utils.day_start_end(user[10])
        self.assertEqual(
            data,
            [
                ['Mon', 0, 0],
                ['Tue', 34745.0, 64792.0],
                ['Wed', 33592.0, 58057.0],
                ['Thu', 38926.0, 62631.0],
                ['Fri', 0, 0],
                ['Sat', 0, 0],
                ['Sun', 0, 0]
            ])

    def test_xml_translator(self):
        """
        Test user data from XML file extraction.
        """
        data = utils.xml_translator()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys()[:3], [36, 165, 170])
        self.assertEqual(
            data.values()[0],
            {
                'name': 'Anna W.',
                'avatar': 'https://intranet.stxnext.pl:443/api/images/users/36'
            }
        )


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
