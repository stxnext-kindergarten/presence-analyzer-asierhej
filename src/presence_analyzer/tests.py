# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals
import os.path
import json
import datetime
import time
import unittest
from collections import OrderedDict

import main  # pylint: disable=relative-import
import utils  # pylint: disable=relative-import
import views  # pylint: disable=unused-import, relative-import
from .utils import memoize

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

    def test_five_top(self):
        """
        Test top 5 workers per months in year.
        """
        resp = self.client.get('/api/v1/five_top/9,2013')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(
            data,
            [
                {
                    'hours': 32,
                    'user_id': 11,
                    'name': 'Maciej D.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/11'
                },
                {
                    'hours': 21,
                    'user_id': 10,
                    'name': 'Maciej Z.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/10'
                }
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
        self.assertItemsEqual(data.keys(), [10, 11, 68, 49, 176, 141, 26, 62])
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

    def test_cache(self):
        """
        Test data caching.
        """
        @memoize(age_cache=20)
        def short_calculation():
            data = 2 + 2
            data = time.time()
            time.sleep(1)
            return data
        self.assertEqual(short_calculation(), short_calculation())

        @memoize(age_cache=1)
        def other_calculation():
            data = 2 + 3
            data = time.time()
            time.sleep(2)
            return data
        self.assertNotEqual(other_calculation(), other_calculation())

    def test_group_by_month(self):
        """
        Test grouping presence entries by month.
        """
        data = utils.group_by_month(utils.get_data(), 2013)
        self.assertEqual(
            data,
            [
                {68: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {
                    10: [
                        [], [], [], [], [], [], [], [], [], [78217], [], [], []
                    ]
                },
                {
                    11: [
                        [], [], [], [], [], [], [],
                        [], [], [118402], [], [], []
                    ]
                },
                {141: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {176: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {49: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {26: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {62: [[], [], [], [], [], [], [], [], [], [], [], [], []]}
            ]
        )
        data = utils.group_by_month(utils.get_data(), 2011)
        self.assertEqual(
            data,
            [
                {68: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {10: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {11: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {141: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {176: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {49: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {26: [[], [], [], [], [], [], [], [], [], [], [], [], []]},
                {62: [[], [], [], [], [], [], [], [], [], [], [], [], []]}
            ]
        )

    def test_five_top_workers(self):
        """
        Test top 5 presence users with information about them.
        """
        data = utils.five_top_workers(9, 1997)
        self.assertEqual(data, [])
        data = utils.five_top_workers(9, 2013)
        self.assertEqual(
            data,
            [
                {
                    'hours': 32, 'user_id': 11, 'name': 'Maciej D.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/11'
                },
                {
                    'hours': 21, 'user_id': 10, 'name': 'Maciej Z.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/10'
                }
            ]
        )
        data = utils.five_top_workers(9, 2015)
        self.assertEqual(
            data,
            [
                {
                    'hours': 15, 'user_id': 62, 'name': 'Damian G.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/62'
                },
                {
                    'hours': 12, 'user_id': 141, 'name': 'Adam P.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/141'
                },
                {
                    'hours': 11, 'user_id': 176, 'name': 'Adrian K.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/176'
                },
                {
                    'hours': 11, 'user_id': 49, 'name': 'Dariusz Ś.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/49'
                },
                {
                    'hours': 8, 'user_id': 68, 'name': 'Damian K.',
                    'avatar':
                    'https://intranet.stxnext.pl:443/api/images/users/68'
                }
            ]
        )

    def test_five_top_user_data(self):
        """
        Test top 5 user data.
        """
        dict_months = [
            (10, [455386]), (11, [263049]), (12, [371559]),
            (13, [394007]), (15, [432795]), (16, [513180]),
            (176, [606888]), (19, [434499]), (165, [555037]),
            (170, [576346]), (23, [514312]), (24, [235634]),
            (141, [612478]), (26, [508050]), (26, [560624]),
            (29, [385973]), (30, []), (31, []), (33, [306667]),
            (36, [546225]), (48, []), (49, []), (54, []), (58, []),
        ]
        sorted_dict = OrderedDict(
            [
                (141, [612478]), (176, [606888]), (170, [576346]),
                (26, [560624]), (165, [555037]), (36, [546225]),
                (23, [514312]), (16, [513180]), (26, [508050]),
                (10, [455386]), (19, [434499]), (15, [432795]),
                (13, [394007]), (29, [385973]), (12, [371559]),
                (33, [306667]), (11, [263049]), (24, [235634]),
                (101, [])
            ]
        )
        data = utils.five_top_user_data(dict_months, sorted_dict)
        self.assertEqual(
            data[0],
            {
                'hours': 170,
                'user_id': 141,
                'name': 'Adam P.',
                'avatar':
                'https://intranet.stxnext.pl:443/api/images/users/141'
            }
        )
        sorted_dict = OrderedDict([(141, [612478])])
        data = utils.five_top_user_data(dict_months, sorted_dict)
        self.assertEqual(data, [])

    def test_sorted_months_dict(self):
        """
        Test sorting of months dict.
        """
        dict_months = [
            (10, [455386]), (11, [263049]), (12, [371559]),
            (13, [394007]), (15, [432795]), (16, [513180]),
            (176, [606888]), (19, [434499]), (165, [555037]),
            (170, [576346]), (23, [514312]), (24, [235634]),
            (141, [612478]), (26, [508050]), (26, [560624]),
            (29, [385973]), (30, []), (31, []), (33, [306667]),
            (36, [546225]), (48, []), (49, []), (54, []), (58, [])
        ]
        data = utils.sorted_months_dict(dict_months)
        self.assertEqual(
            data,
            OrderedDict(
                [
                    (141, [612478]), (176, [606888]), (170, [576346]),
                    (26, [508050]), (165, [555037]), (36, [546225]),
                    (23, [514312]), (16, [513180]), (10, [455386]),
                    (19, [434499]), (15, [432795]), (13, [394007]),
                    (29, [385973]), (12, [371559]), (33, [306667]),
                    (11, [263049]), (24, [235634]), (30, []), (31, []),
                    (48, []), (49, []), (54, []), (58, [])
                ]
            )
        )

    def test_months_sum_dict(self):
        """
        Test appending and suming time for every month.
        """
        items = {
            178:
            {
                datetime.date(2013, 9, 9):
                {
                    'end': datetime.time(17, 14, 42),
                    'start': datetime.time(11, 43, 50)
                }
            },
            179:
            {
                datetime.date(2013, 9, 12):
                {
                    'end': datetime.time(18, 5, 24),
                    'start': datetime.time(16, 55, 24)
                }
            }
        }
        item = datetime.date(2013, 9, 9)
        months = [[] for month in xrange(13)]
        data = utils.months_sum_dict(2013, items, item, 178, months)
        self.assertEqual(
            data,
            [
                [], [], [], [], [], [], [], [], [], [19852], [], [], []
            ]
        )

    def test_user_validate(self):
        """
        Test checking if user exist.
        """
        months_sum = [
            [], [], [], [], [], [], [550395], [632015],
            [505118], [499105], [486939], [624356], [455386]
        ]
        data = utils.user_validate(months_sum, 34654)
        self.assertEqual(data, [])
        data = utils.user_validate(months_sum, 141)
        self.assertEqual(
            data,
            {
                141: [
                    [], [], [], [], [], [], [550395], [632015],
                    [505118], [499105], [486939], [624356], [455386]
                ]
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
