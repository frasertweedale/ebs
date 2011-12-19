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

from . import estimator
from . import task


_today = datetime.date.today()
_tomorrow = _today + datetime.timedelta(days=1)
_yesterday = _today - datetime.timedelta(days=1)


class EstimatorTestCase(unittest.TestCase):
    def test_from_dict(self):
        """Test instantiation from a dict."""
        with self.assertRaisesRegexp(TypeError, r'\bname\b'):
            e = estimator.Estimator.from_dict({})

        e = estimator.Estimator.from_dict({'name': 'Bob'})
        self.assertEqual(e.name, 'Bob')
        self.assertSequenceEqual(e.tasks, ())
        self.assertSequenceEqual(e.events, ())

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [
                {'estimate': 4, 'description': 'Task 1'},
                {'estimate': 2, 'actual': 3, 'description': 'Task 2'},
            ],
            'events': [
                {'date': _today, 'cost': 2, 'description': 'Foo'}
            ]
        })
        self.assertListEqual(
            e.tasks,
            [
                task.Task(estimate=4, description='Task 1'),
                task.Task(estimate=2, actual=3, description='Task 2'),
            ]
        )
        self.assertListEqual(
            e.events,
            [
                task.Event(date=_today, cost=2, description='Foo')
            ]
        )

    def test_eq(self):
        data = {
            'name': 'Bob',
            'tasks': [
                {'estimate': 4, 'date': _yesterday, 'description': 'Task 1'},
                {'estimate': 2, 'actual': 3, 'description': 'Task 2'},
            ],
            'events': [
                {'date': _today, 'cost': 2, 'description': 'Foo'}
            ]
        }
        self.assertEqual(
            estimator.Estimator.from_dict(data),
            estimator.Estimator.from_dict(data)
        )

    def test_velocities(self):
        """Test the velocities method."""
        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4}, {'estimate': 2}]
        })
        self.assertItemsEqual(e.velocities(), [])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4}, {'estimate': 2, 'actual': 4}]
        })
        self.assertItemsEqual(e.velocities(), [0.5])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'actual': 4}, {'estimate': 2}]
        })
        self.assertItemsEqual(e.velocities(), [1])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [
                {'estimate': 4, 'actual': 2},
                {'estimate': 2, 'actual': 2}
            ]
        })
        self.assertItemsEqual(e.velocities(), [1, 2])

    def test_velocities_with_max_age(self):
        _30d_ago = _today - datetime.timedelta(days=30)
        _31d_ago = _today - datetime.timedelta(days=31)

        _30d = datetime.timedelta(days=30)

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'date': _today, 'actual': 2}]
        })
        self.assertItemsEqual(e.velocities(max_age=_30d), [2])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'date': _30d_ago, 'actual': 2}]
        })
        self.assertItemsEqual(e.velocities(max_age=_30d), [2])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'date': _31d_ago, 'actual': 2}]
        })
        self.assertItemsEqual(e.velocities(max_age=_30d), [])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'date': _30d_ago, 'actual': 2}]
        })
        self.assertItemsEqual(e.velocities(max_age=-_30d), [2])

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [{'estimate': 4, 'date': _31d_ago, 'actual': 2}]
        })
        self.assertItemsEqual(e.velocities(max_age=-_30d), [])

    def test_simulate_future(self):
        """Test simulations of the future."""
        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [
                {'estimate': 4, 'actual': 2},
                {'estimate': 2, 'actual': 2},
                {'estimate': 2, 'actual': 4},
                {'estimate': 8},
                {'estimate': 1},
            ]
        })
        possible_futures = set([
            frozenset((0.5, 4)), frozenset((0.5, 8)), frozenset((0.5, 16)),
            frozenset((1, 4)), frozenset((1, 8)), frozenset((1, 16)),
            frozenset((2, 4)), frozenset((2, 8)), frozenset((2, 16)),
        ])
        encountered_futures = set()
        # simulate until all possible futures have been encountered
        while encountered_futures < possible_futures:
            future = e.simulate_future()
            self.assertEqual(len(future), 2)
            future = frozenset(future)
            self.assertIn(future, possible_futures)
            encountered_futures.add(future)
        self.assertSetEqual(possible_futures, encountered_futures)

    def test_simulate_future_with_priority(self):
        """Simulate the future with some tasks filtered by priority."""
        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [
                {'estimate': 2, 'actual': 2},
                {'estimate': 8},
                {'estimate': 1, 'priority': 3},
            ]
        })
        future = e.simulate_future(priority=2)
        self.assertItemsEqual(future, [8])
        future = e.simulate_future(priority=3)
        self.assertItemsEqual(future, [8, 1])

    def test_simulate_future_with_max_age(self):
        """Simulate a future, ignoring some estimates due to old age."""
        _30d_ago = _today - datetime.timedelta(days=30)
        _31d_ago = _today - datetime.timedelta(days=31)

        _30d = datetime.timedelta(days=30)

        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'tasks': [
                {'estimate': 4, 'actual': 2, 'date': _31d_ago},
                {'estimate': 2, 'actual': 2, 'date': _30d_ago},
                {'estimate': 2, 'actual': 4, 'date': _today},
                {'estimate': 8},
                {'estimate': 1},
            ]
        })
        possible_futures = set([
            frozenset((1, 8)), frozenset((1, 16)),
            frozenset((2, 8)), frozenset((2, 16)),
        ])
        encountered_futures = set()
        # simulate until all possible futures have been encountered
        while encountered_futures < possible_futures:
            future = e.simulate_future(max_age=_30d)
            self.assertEqual(len(future), 2)
            future = frozenset(future)
            self.assertIn(future, possible_futures)
            encountered_futures.add(future)
        self.assertSetEqual(possible_futures, encountered_futures)

    def test_future_events(self):
        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'events': [
                {'date': _today,  'cost': 1},
                {'date': _tomorrow,  'cost': 3},
                {'date': _yesterday, 'cost': 5},
            ]
        })
        self.assertListEqual(sorted(e.future_events), sorted([
            task.Event(date=_today, cost=1),
            task.Event(date=_tomorrow, cost=3)
        ]))

    def test_future_event_cost(self):
        e = estimator.Estimator.from_dict({
            'name': 'Bob',
            'events': [
                {'date': _today,  'cost': 1},
                {'date': _today,  'cost': 3},
                {'date': _yesterday, 'cost': 5},
            ]
        })
        self.assertEqual(e.future_event_cost, 4)
