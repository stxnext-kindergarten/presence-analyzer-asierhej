# -*- coding: utf-8 -*-
"""
Defines views.
"""
import calendar
import logging

from flask import abort
# pylint: disable=import-error
from flask_mako import MakoTemplates, render_template

from presence_analyzer.main import app
from presence_analyzer.utils import (
    day_start_end,
    get_data,
    group_by_weekday,
    jsonify,
    mean,
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


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

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
        log.debug('User %s not found!', user_id)
        abort(404)

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
        log.debug('User %s not found!', user_id)
        abort(404)

    return day_start_end(data[user_id])
