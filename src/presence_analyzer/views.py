# -*- coding: utf-8 -*-
"""
Defines views.
"""
import calendar
import logging

# pylint: disable=import-error
from flask_mako import MakoTemplates, render_template

from presence_analyzer.main import app
from presence_analyzer.utils import (
    day_start_end,
    five_top_workers,
    get_data,
    group_by_weekday,
    jsonify,
    mean,
    podium_data_maker,
    xml_translator
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name
mako = MakoTemplates(app)  # pylint: disable=invalid-name


@app.route('/', defaults={'where': 'presence_weekday.html'})
@app.route('/<where>')
def redirect_mako(where):
    """
    Redirects to pages.
    """
    try:
        return render_template(where, name=mako)
    except Exception:  # pylint: disable=broad-except
        return render_template('not_found.html', name=mako)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = xml_translator()
    return [
        {'user_id': i, 'name': data[i]['name'], 'avatar': data[i]['avatar']}
        for i in data.keys()
    ]


@app.route('/api/v1/months', methods=['GET'])
@jsonify
def months_view():
    """
    Month list for dropdown.
    """
    data = get_data()
    years = []
    years_on = []
    for user in data:
        year = data[user].items()[0][0].year
        if year in years_on:
            pass
        else:
            years.append(('year', year))
            years_on.append(year)
    years = sorted(years, key=lambda year: year[1])
    months = []
    for month in list(enumerate(calendar.month_abbr[1:])):
        months.append({'number': month[0], 'name': month[1]})
    result = []
    for year in years:
        for month in months:
            data = dict(month.items() + [year])
            result.append(data)
    return result


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        return 'no data'

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        return 'no data'

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end(user_id):
    """
    The medium time to come to the office and medium time of leave.
    """
    data = get_data()
    if user_id not in data:
        return 'no data'

    return day_start_end(data[user_id])


@app.route('/api/v1/podium/<int:user_id>', methods=['GET'])
@jsonify
def podium(user_id):
    """
    Five best months of work time.
    """
    data = get_data()
    if user_id not in data:
        return 'no data'

    return podium_data_maker(data[user_id])


@app.route('/api/v1/five_top/<month_year>', methods=['GET'])
@jsonify
def five_top(month_year):
    """
    Top 5 workers per months in year.
    """
    data = month_year.split(',')
    return five_top_workers(int(data[0]), int(data[1]))
