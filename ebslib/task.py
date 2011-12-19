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
import functools


class NotCompletedError(Exception):
    pass


class Task(object):
    """A task with an estimated and actual cost.

    Completion of a task is indicated by an actual cost (which
    declares what the task actually cost.

    Cost could mean anything but in a scheduling context would
    represent time (e.g. in hours).
    """

    __slots__ = frozenset([
        'id', 'priority', 'estimate', 'date', 'actual', 'description'
    ])

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __init__(self,
        id=None, description=None, priority=None,
        estimate=0, date=None, actual=0
    ):
        """Initialise the task

        ``id``
          Optional task ID.  If supplied, must be unique.
        ``description``
          Optional description of the task.
        ``priority``
          Optional task priority.  Any natural number may be used; ``1``
          is the highest priority.
        ``estimate``
          The estimated cost.
        ``date``
          Optional ``datetime.date`` on which the estimate was made.
          May be used to filter old estimates.
        ``actual``
          The actual cost.  Zero implies that the task has not been
          completed.
        """
        self.id = id
        self.description = description
        self.priority = priority
        self.estimate = estimate
        self.date = date
        self.actual = actual

    @property
    def completed(self):
        """Return whether the task is completed or not."""
        return self.actual

    @property
    def velocity(self):
        """Return the velocity for this task.

        Raise NotCompletedError if the task is not completed.
        """
        if not self.completed:
            raise NotCompletedError
        return self.estimate / self.actual

    def __eq__(self, other):
        return type(self) == type(other) and all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__slots__
        )

    def __ne__(self, other):
        return not self.__eq__(other)


@functools.total_ordering
class Event(object):
    """An event with a date and an absolute cost.

    An event remains relevant until its date has passed, and has
    an absolute cost.  Cost could represent anything, but in a
    scheduling context would represent a time (perhaps in hours)
    that will be lost (e.g. due to leave or other activities known
    ahead of time.
    """

    __slots__ = frozenset(['date', 'cost', 'description'])

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __init__(self, date=None, cost=0, description=None):
        """Initialise the event.

        ``date``
          The date of the event.
        ``cost``
          The cost of the event.
        ``description``
          An optional description of the event.
        """
        self.date = date or datetime.date.today()
        self.cost = cost
        self.description = description

    @property
    def completed(self):
        """Determine whether this event is completed or not."""
        return self.date < datetime.date.today()

    def __eq__(self, other):
        return type(self) == type(other) and all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self.__slots__
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        _self = tuple(getattr(self, attr) for attr in self.__slots__)
        _other = tuple(getattr(other, attr) for attr in self.__slots__)
        return _self < _other

    def __repr__(self):
        return '{!r}({})'.format(
            type(self),
            ', '.join(
                '{}={!r}'.format(attr, getattr(self, attr))
                for attr in self.__slots__
            )
        )
