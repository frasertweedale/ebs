# This file is part of ebs
# Copyright (C) 2011, 2012 Fraser Tweedale, Benon Technologies Pty Ltd
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
                and t.actual    # exclude tasks with no actual
        ]

    def _fn_velocity(self, f, **kwargs):
        try:
            return f(self.velocities(**kwargs))
        except:
            raise NoHistoryError(
                "Estimator '{}' has no useful estimation history."
                .format(self.name)
            )

    def min_velocity(self, **kwargs):
        return self._fn_velocity(min, **kwargs)

    def max_velocity(self, **kwargs):
        return self._fn_velocity(max, **kwargs)

    def mean_velocity(self, **kwargs):
        return self._fn_velocity(lambda x: sum(x) / len(x), **kwargs)

    def stddev_velocity(self, **kwargs):
        velocities = self.velocities(**kwargs)
        N = len(velocities)
        mu = self.mean_velocity()
        return math.sqrt(sum((x - mu) ** 2 for x in velocities) / N)

    def simulate_future(self, project=None, max_age=None, priority=None):
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
                if not (priority and t.priority and t.priority > priority)
                    and (not project or t.project == project)
            ]
        except IndexError:
            raise NoHistoryError(
                "Estimator '{}' has no useful estimation history."
                .format(self.name)
            )

    def simulate_futures(self, **kwargs):
        """Generate simulated outcomes."""
        while True:
            yield self.simulate_future(**kwargs)

    def get_events(self, start=None, stop=None):
        """Generate the estimators events, optionally filtered by date.

        Return a generator of events.  If start is given, return events
        occuring on or after the given date.  If stop is given, return
        events occuring before the given date.
        """
        return (
            e for e in self.events
            if (not start or e.date >= start) and (not stop or e.date < stop)
        )

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
