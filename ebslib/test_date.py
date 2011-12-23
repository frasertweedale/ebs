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

import datetime
import unittest

from . import date
from . import task

_today = datetime.date.today()


class DateTestCase(unittest.TestCase):
    def test_work_date_ceil_with_empty_work_days(self):
        with self.assertRaisesRegexp(ValueError, r'\bwork_days\b'):
            date.work_date_ceil([], _today)

    def test_work_date_ceil_with_bogus_work_days(self):
        with self.assertRaisesRegexp(ValueError, r'\bwork_days\b'):
            date.work_date_ceil(['a', 'b', 'c'], _today)

    def test_work_date_ceil(self):
        work_days = frozenset([0, 1, 2, 3, 4])
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            offset = 0
            if _now.weekday() == 5:
                offset = 2
            elif _now.weekday() == 6:
                offset = 1
            self.assertEqual(
                date.work_date_ceil(work_days, _now),
                _today + datetime.timedelta(days=offset + i)
            )

    def test_apply_work_date_interval(self):
        work_days = frozenset([0, 1, 2, 3, 4])
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            # offsets for each day for an interval of 3
            offsets = [3, 3, 5, 5, 5, 4, 3]
            if _now.weekday() == 5:
                offset = 2
            elif _now.weekday() == 6:
                offset = 1
            self.assertEqual(
                date.apply_work_date_interval(work_days, _now, 3),
                _now + datetime.timedelta(days=offsets[_now.weekday()])
            )
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            # offsets for each day for an interval of 9.5
            offsets = [14, 14, 14, 14, 14, 13, 12]
            if _now.weekday() == 5:
                offset = 2
            elif _now.weekday() == 6:
                offset = 1
            self.assertEqual(
                date.apply_work_date_interval(work_days, _now, 9.5),
                _now + datetime.timedelta(days=offsets[_now.weekday()])
            )

    def test_ship_date_type(self):
        with self.assertRaisesRegexp(TypeError, r'\bhours\b'):
            date.ship_date(hours_per_day=10)
        with self.assertRaisesRegexp(TypeError, r'\bhours_per_day\b'):
            date.ship_date(hours=10)
        with self.assertRaisesRegexp(ValueError, r'\bhours_per_day\b'):
            date.ship_date(hours=10, hours_per_day=0)
        with self.assertRaisesRegexp(ValueError, r'\bhours_per_day\b'):
            date.ship_date(hours=10, hours_per_day=-1)
        date.ship_date(hours=10, hours_per_day=1)

    def test_ship_date(self):
        work_days = frozenset([0, 1, 2, 3, 4])
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            # offsets for each day for an interval of 3
            offsets = [3, 3, 5, 5, 5, 4, 3]
            self.assertEqual(
                date.ship_date(
                    work_days=work_days,
                    hours=3,
                    hours_per_day=1,
                    start_date=_now
                ),
                (_now + datetime.timedelta(days=offsets[_now.weekday()]), 0)
            )
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            # offsets for each day for an interval of 9.5
            offsets = [14, 14, 14, 14, 14, 13, 12]
            self.assertEqual(
                date.ship_date(
                    work_days=work_days,
                    hours=70.2,
                    hours_per_day=7.6,
                    start_date=_now
                ),
                (_now + datetime.timedelta(days=offsets[_now.weekday()]), 5.8)
            )

    def test_ship_date_with_zero_hours(self):
        work_days = frozenset([0, 1, 2, 3, 4])
        self.assertEqual(
            date.ship_date(
                work_days=work_days,
                hours=0,
                hours_per_day=1,
                start_date=_today
            ),
            (_today, 0)
        )

    def test_ship_date_with_negative_hours(self):
        work_days = frozenset([0, 1, 2, 3, 4])
        for hours in -0.1, -0.9, -1, -1.1:
            self.assertEqual(
                date.ship_date(
                    work_days=work_days,
                    hours=hours,
                    hours_per_day=1,
                    start_date=_today
                ),
                (_today, 0)
            )

    def test_ship_date_with_events(self):
        work_days = frozenset([0, 1, 2, 3, 4])

        def event_in_n_work_days(start, n):
            return task.Event(
                date=date.apply_work_date_interval(work_days, start, n),
                cost=1
            )
        for i in range(14):
            _now = _today + datetime.timedelta(days=i)
            events = [
                event_in_n_work_days(_now, 1),
                event_in_n_work_days(_now, 2),
                event_in_n_work_days(_now, 10),  # far away; should be excluded
            ]
            offsets = [3, 3, 5, 5, 5, 4, 3]
            # offsets for each day for an interval of 3
            self.assertEqual(
                date.ship_date(
                    work_days=work_days,
                    hours=1,
                    events=events,
                    hours_per_day=1,
                    start_date=_now,
                ),
                (_now + datetime.timedelta(days=offsets[_now.weekday()]), 0)
            )
