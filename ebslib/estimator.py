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
import math
import random

from . import task


class NoHistoryError(Exception):
    """The estimator has no useful estimation history."""


class Estimator(object):
    """An estimator."""

    __slots__ = frozenset(['name', 'tasks', 'events'])

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if 'tasks' in data:
            data['tasks'] = [task.Task.from_dict(x) for x in data['tasks']]
        if 'events' in data:
            data['events'] = [task.Event.from_dict(x) for x in data['events']]
        return cls(**data)

    def __init__(self, name=None, tasks=None, events=None):
        tasks = tasks or []
        events = events or []
        if not name:
            raise TypeError("Argument 'name' not supplied.")
        self.name = name
        self.tasks = tasks
        self.events = events

    def completed_tasks(self):
        """Generate completed tasks."""
        return (t for t in self.tasks if t.completed)

    def pending_tasks(self):
        """Generate incomplete tasks."""
        return (t for t in self.tasks if not t.completed)

    def velocities(self, max_age=None):
        """Return the estimator's velocities.

        ``max_age``
          Optional ``datetime.timedelta`` to limit the velocities
          to a maximum age.

        Return a sequence of velocities.
        """
        _today = datetime.date.today()
        return [
            t.estimate / t.actual
            for t in self.completed_tasks()
            if not (max_age and t.date and _today - t.date > abs(max_age))
                and t.estimate  # exclude tasks with no estimate
        ]

    def min_velocity(self, max_age=None):
        return min(self.velocities(max_age))

    def max_velocity(self, max_age=None):
        return max(self.velocities(max_age))

    def mean_velocity(self, max_age=None):
        velocities = self.velocities(max_age)
        return sum(velocities) / len(velocities)

    def stddev_velocity(self, max_age=None):
        velocities = self.velocities(max_age)
        N = len(velocities)
        mu = self.mean_velocity()
        return math.sqrt(sum((x - mu) ** 2 for x in velocities) / N)

    def simulate_future(self, max_age=None, priority=None):
        """Simulate the future once.

        This implements one round of a Monte Carlo simulation.  The
        estimate of each non-completed task is divided by a randomly
        selected velocity and this list of numbers is returned.

        ``max_age``
          Optional maximum age of previous estimates to be used in the
          simulation.
        ``priority``
          Optional priority threshold; uncompleted tasks of a lower
          priority will be omitted from the simulation.
        """
        velocities = self.velocities(max_age)
        try:
            return [
                t.estimate / random.choice(velocities)
                for t in self.pending_tasks()
                if not (t.priority and t.priority > priority)
            ]
        except IndexError:
            raise NoHistoryError(
                "Estimator '{}' has no useful estimation history."
                .format(self.name)
            )

    def simulate_futures(self, max_age=None):
        """Generate simulated outcomes."""
        while True:
            yield self.simulate_future(max_age)

    @property
    def future_events(self):
        """Return this estimator's future events."""
        return [x for x in self.events if not x.completed]

    @property
    def future_event_cost(self):
        """Calculate the total cost of future events."""
        return sum(e.cost for e in self.future_events)

    def __eq__(self, other):
        return type(self) == type(other) and all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__slots__
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '{!r}({})'.format(
            type(self),
            ', '.join(
                '{}={!r}'.format(attr, getattr(self, attr))
                for attr in self.__slots__
            )
        )
