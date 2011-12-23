# This file is part of ebs
# Copyright (C) 2011 Fraser Tweedale, Benon Technologies Pty Ltd
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

import collections
import datetime
import math


def ship_date(
    work_days=frozenset([0, 1, 2, 3, 4]),
    hours=None,
    events=(),
    hours_per_day=None,
    start_date=None
):
    """Calculate the projected ship date.

    Given pending hours, calculate a ship date.

    ``work_days``
      The days of the week that count as work days.
      Defaults to 1..5 (Monday to Friday).
    ``hours``
      The hours of tasks remaining.
    ``events``
      An optional sequence of events.
    ``hours_per_day``
      The number of hours in a day that can be devoted to
      completion of tasks and events.

    Return a tuple of the calculated ship date and the hours remaining
    on the calculated ship date, in that order.
    """
    start_date = start_date or datetime.date.today()
    if hours is None:
        raise TypeError("Argument 'hours' must be supplied.")
    if hours_per_day is None:
        raise TypeError("Argument 'hours_per_day' must be supplied.")
    if hours_per_day <= 0:
        raise ValueError("Argument 'hours_per_day' must be greater than zero.")
    if not isinstance(events, collections.Sequence):
        raise TypeError("Argument 'events' is not a Sequence.")
    hours = max(hours, 0)
    days = hours / hours_per_day
    remaining = \
        round((hours_per_day - (hours % hours_per_day)) % hours_per_day, 3)
    ship = apply_work_date_interval(work_days, start_date, days)
    if events:
        return _add_events(
            start_date, ship,
            remaining, events, hours_per_day
        )
    return ship, remaining


def _add_events(
    start, end,
    hours_remaining,
    events, hpd
):
    """Mix a events into an estimate.

    This method takes the start date from which the estimate is being
    made, the estimated completion date and the number of hours
    remaining on that date, a sequence of events and the hours per day.

    ``start``
      Search for events starting from the given date.
    ``end``
      Estimated date.  Used as upper bound for events.
    ``hours_remaining``
      Hours remaining on the estimated date.
    ``events``
      A Sequence of events.
    ``hours_per_day``
      The number of hours per day.
    """
    event_hours = sum(
        e.cost for e in events
        if e.date > start and e.date <= end
    )
    new_end, new_hours_remaining = ship_date(
        hours=event_hours - hours_remaining,
        hours_per_day=hpd,
        start_date=end
    )
    if new_end == end:
        return end, new_hours_remaining
    return _add_events(end, new_end, new_hours_remaining, events, hpd)


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
