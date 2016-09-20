# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
import calendar
import csv
import logging
import time
import threading
from collections import OrderedDict
from datetime import datetime
from functools import wraps

import xml.etree.ElementTree as ET
from json import dumps
from flask import Response

from presence_analyzer.main import app


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
storage_cache = {}
lock = threading.Lock()


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def memoize(storage=storage_cache, age_cache=0):
    """
    Caching function.
    """
    def _memoize(function):
        with lock:
            def __memoize(*args, **kw):
                key = function.__name__
                try:
                    expired = (
                        age_cache != 0 and
                        (storage[key]['expire_time'] + age_cache) <
                        time.time())
                except KeyError:
                    expired = True
                if not expired:
                    return storage[key]['values']
                storage[key] = {
                    'expire_time': time.time(),
                    'values': function(*args, **kw)
                }
                return storage[key]['values']
            return __memoize
    return _memoize


@memoize(age_cache=600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.
    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}
    return data


def xml_translator():
    """
    Extracts user data from XML file.
    """
    tree = ET.parse(app.config['XML_DATA'])
    root = tree.getroot()
    root_server = root.find('server')
    protocol = root_server.find('protocol').text
    host = root_server.find('host').text
    port = root_server.find('port').text
    url = protocol + '://' + host + ':' + port
    root_user = [root.find('users')]
    data = {}
    for user in root_user[0].findall('user'):
        name = user.find('name').text
        avatar = user.find('avatar').text
        id_user = user.get('id')
        data[int(id_user)] = {'name': name, 'avatar': url + avatar}
    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(date):
    """
    Calculates amount of seconds since midnight.
    """
    return date.hour * 3600 + date.minute * 60 + date.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def day_start_end(items):
    """
    Groups times of start and end work at weekday.
    """
    weekdays = [[] for day in xrange(7)]
    for date in items:
        start = seconds_since_midnight(items[date]['start'])
        end = seconds_since_midnight(items[date]['end'])
        weekdays[date.weekday()].append([start, end])
    days = calendar.day_abbr
    results = []
    for day in days:
        start = []
        end = []
        for item in weekdays[len(results)]:
            if item != []:
                start.append(item[0])
                end.append(item[1])
        results.append([day, mean(start), mean(end)])
    return results


def podium_data_maker(user):
    """
    Groups presence entries as podium data.
    """
    months = [[] for month in xrange(12)]
    for item in user:
        start = user[item]['start']
        end = user[item]['end']
        months[item.month].append(interval(start, end))
        months[item.month] = [sum(months[item.month])]
    results = podium_result_structure_builder(months)
    return sorted(results, key=lambda time: time[1])


def podium_result_structure_builder(months):
    """
    Building results for podium template.
    """
    results = []
    for item in months:
        try:
            results.append(
                [
                    calendar.month_name[months.index(item)],
                    item[0] / 3600
                ]
            )
        except:
            results.append(['no data', 0])
    return results


def months_sum_dict(year, items, item, user, months):
    """
    Append and sum time for every month.
    """
    if item.year == year:
        start = items[user][item]['start']
        end = items[user][item]['end']
        months[item.month].append(interval(start, end))
        months[item.month] = [sum(months[item.month])]
    else:
        pass
    return months


def user_validate(months_sum, user):
    """
    Check if user exist.
    """
    result = []
    try:
        xml_translator()[user]
        if months_sum == []:
            pass
        else:
            result.append({user: months_sum})
            result = result[0]
    except:
        pass
    return result


def group_by_month(items, year):
    """
    Groups presence entries by month.
    """
    results = []
    for user in items:
        months = [[] for month in xrange(13)]
        for item in items[user]:
            months_sum = months_sum_dict(year, items, item, user, months)
        results.append(user_validate(months_sum, user))
    return results


def sorted_months_dict(dict_months):
    """
    Sort months dict.
    """
    sorted_dict = OrderedDict(
        sorted(
            dict_months,
            key=lambda x: x[1],
            reverse=True
        )
    )
    return sorted_dict


def five_top_user_data(dict_months, sorted_dict):
    """
    Collect data and append it to the top 5 user.
    """
    id_top = list(sorted_dict.keys())[:5]
    results = []
    for item in id_top:
        if dict(dict_months)[item] == 0 or len(id_top) < 5:
            return results
        else:
            try:
                results.append(
                    {
                        'user_id': item,
                        'hours': dict(dict_months)[item][0] / 3600,
                        'name': xml_translator()[item]['name'],
                        'avatar': xml_translator()[item]['avatar']
                    }
                )
            except:
                return results
    return results


def five_top_workers(month, year):
    """
    Top 5 presence users with information about them.
    """
    dict_months = []
    monthly_grouped = group_by_month(get_data(), year)
    for user in monthly_grouped:
        try:
            dict_months.append((user.items()[0][0], user.items()[0][1][month]))
        except:
            pass
    sorted_dict = sorted_months_dict(dict_months)
    return five_top_user_data(dict_months, sorted_dict)
