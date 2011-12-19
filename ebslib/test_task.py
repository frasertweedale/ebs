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

from __future__ import division

import datetime
import unittest

from . import task


_today = datetime.date.today()
_tomorrow = _today + datetime.timedelta(days=1)
_yesterday = _today - datetime.timedelta(days=1)


class TaskTestCase(unittest.TestCase):
    def test_from_dict(self):
        t = task.Task.from_dict({
            'estimate': 4,
            'date': _yesterday,
            'description': 'Do something'
        })
        self.assertEqual(t.estimate, 4)
        self.assertEqual(t.date, _yesterday)
        self.assertEqual(t.actual, 0)
        self.assertEqual(t.description, 'Do something')

    def test_eq(self):
        data = dict(
            id=1234, description='Foo', priority=1,
            estimate=1, date=_today, actual=2
        )
        self.assertEqual(task.Task.from_dict(data), task.Task.from_dict(data))
        self.assertSetEqual(set(data.viewkeys()), task.Task.__slots__)

    def test_ne(self):
        # check one differing attribute at a time
        data = dict(
            id=1, description='Foo', priority=0,
            estimate=1, date=_today, actual=2
        )
        other_data = dict(
            id=None, description='Bar', priority=1,
            estimate=2, date=_yesterday, actual=1
        )
        checked_attrs = set()
        t = task.Task.from_dict(data)
        for key in data:
            _data = dict(data)
            _data.update({key: other_data[key]})
            self.assertNotEqual(t, task.Task.from_dict(_data))
            checked_attrs.add(key)
        self.assertSetEqual(checked_attrs, task.Task.__slots__)

    def test_completed(self):
        t = task.Task(estimate=1)
        self.assertFalse(t.completed)
        t = task.Task(estimate=1, actual=0)
        self.assertFalse(t.completed)
        t = task.Task(estimate=1, actual=2)
        self.assertTrue(t.completed)

    def test_velocity(self):
        t = task.Task(estimate=5, actual=0)
        with self.assertRaises(task.NotCompletedError):
            t.velocity
        t.actual = 6
        self.assertEqual(t.velocity, 5 / 6)
        t.actual = 5
        self.assertEqual(t.velocity, 5 / 5)
        t.actual = 4
        self.assertEqual(t.velocity, 5 / 4)


class EventTestCase(unittest.TestCase):
    def test_from_dict(self):
        t = task.Event.from_dict({
            'date': _today,
            'description': 'Do something'
        })
        self.assertEqual(t.date, _today)
        self.assertEqual(t.cost, 0)
        self.assertEqual(t.description, 'Do something')

    def test_eq(self):
        self.assertEqual(
            task.Event(date=_today, cost=2, description='Foo'),
            task.Event(date=_today, cost=2, description='Foo')
        )

    def test_ne(self):
        # check one differing attribute at a time
        t = task.Event(date=1, cost=2, description='Foo'),
        self.assertNotEqual(
            t,
            task.Event(date=_today, cost=2, description='Bar')
        )
        self.assertNotEqual(
            t,
            task.Event(date=_today, cost=1, description='Foo')
        )
        self.assertNotEqual(
            t,
            task.Event(date=_tomorrow, cost=2, description='Foo')
        )

    def test_completed(self):
        t = task.Event(date=_tomorrow)
        self.assertFalse(t.completed)
        t = task.Event(date=_today)
        self.assertFalse(t.completed)
        t = task.Event(date=_yesterday)
        self.assertTrue(t.completed)
