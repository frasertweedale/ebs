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

    def test_calculate_date_type(self):
        with self.assertRaisesRegexp(TypeError, r'\btask_hours_per_day\b'):
            date.ship_date(task_hours=10)
        with self.assertRaisesRegexp(TypeError, r'\bevent_hours_per_day\b'):
            date.ship_date(event_hours=10)
        date.ship_date(task_hours=10, task_hours_per_day=10)
        date.ship_date(event_hours=10, event_hours_per_day=10)

    def test_calculate_date(self):
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
                date.ship_date(
                    work_days=work_days,
                    task_hours=3,
                    task_hours_per_day=1,
                    start_date=_now
                ),
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
                date.ship_date(
                    work_days=work_days,
                    task_hours=55,
                    task_hours_per_day=7.3,
                    event_hours=15.2,
                    event_hours_per_day=7.6,
                    start_date=_now
                ),
                _now + datetime.timedelta(days=offsets[_now.weekday()])
            )
