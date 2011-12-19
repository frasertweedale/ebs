# This file is part of ebs
# Copyright (C) 2011 Fraser Tweedale
#
# ebs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Date and time utility functions."""

from __future__ import division

import datetime
import math


def ship_date(
    work_days=frozenset([0, 1, 2, 3, 4]),
    task_hours=0,
    task_hours_per_day=0,
    event_hours=0,
    event_hours_per_day=0,
    start_date=None
):
    """Calculate the projected ship date.

    Given task and event hours, calculate a ship date.

    ``work_days``
      The days of the week that count as work days.
      Defaults to 1..5 (Monday to Friday).
    ``task_hours``
      The hours of tasks remaining.  Defaults to zero.
    ``task_hours_per_day``
      The number of hours in a day that can be devoted to
      completion of tasks.
    ``event_hours``
      The hours of events remaining.  Defaults to zero.
    ``event_hours_per_day``
      The number of hours in a day that can be devoted to
      events.
    """
    start_date = start_date or datetime.date.today()
    if task_hours and not task_hours_per_day:
        raise TypeError(
            "Argument 'task_hours_per_day' must be supplied when "
            "'task_hours' is supplied."
        )
    if event_hours and not event_hours_per_day:
        raise TypeError(
            "Argument 'event_hours_per_day' must be supplied when "
            "'event_hours' is supplied."
        )
    days = 0
    if task_hours:
        days += task_hours / task_hours_per_day
    if event_hours:
        days += event_hours / event_hours_per_day
    return apply_work_date_interval(work_days, start_date, days)


def work_date_ceil(work_days, date):
    """Return the next work date on or after the given date."""
    # try at most 7 times, then explode
    for i in range(7):
        new_date = date + datetime.timedelta(days=i)
        if new_date.weekday() in work_days:
            return new_date
    raise ValueError("Argument 'work_days' is invalid.")


def apply_work_date_interval(work_days, start, interval):
    _cur = work_date_ceil(work_days, start)
    interval = interval if _cur == start else interval - 1
    for i in range(int(math.ceil(interval))):
        _cur = work_date_ceil(work_days, _cur + datetime.timedelta(days=1))
    return _cur
