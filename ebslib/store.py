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
import json
import os.path

from . import estimator


def _serialise(obj):
    if isinstance(obj, datetime.date):
        return dict(__date__=True, ymd=[obj.year, obj.month, obj.day])
    return {attr: getattr(obj, attr) for attr in obj.__slots__}


def _object_hook(dict):
    if '__date__' in dict:
        return datetime.date(*dict['ymd'])
    return dict


def write(fp, data):
    """Write the data to the given file."""
    json.dump(data, fp, default=_serialise)


def read(fp):
    """Read data from the given file."""
    return [
        estimator.Estimator.from_dict(x)
        for x in json.load(fp, object_hook=_object_hook)
    ]


class Store(object):
    """A data store.

    A store is a context manager that reads data from a file and
    writes its data back to that file.

    Data is accessed via the ``data`` attribute.  It may be reset by
    invoking ``del store.data``.  The ``data`` attribute may not be
    set.
    """

    __slots__ = ('_filename', '_data')

    def __init__(self, filename):
        self._data = None
        self._filename = os.path.expanduser(filename)

    @property
    def data(self):
        if self._data is None:
            try:
                with open(self._filename) as fp:
                    self._data = read(fp)
            except IOError:
                self._data = []
        return self._data

    @data.deleter
    def data(self):
        self._data = None

    def flush(self):
        if self._data is not None:
            with open(self._filename, 'w') as fp:
                write(fp, self._data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.flush()

    @property
    def estimators(self):
        return self.data

    def get_estimator(self, name):
        """Get an estimator by name."""
        self.assert_estimator_exist(name)
        return [e for e in self.estimators if e.name == name][0]

    def estimator_exists(self, name):
        """Return whether the named estimator exists in the data store."""
        return any(e.name == name for e in self.estimators)

    def assert_estimator_exist(self, name):
        if not self.estimator_exists(name):
            raise UserWarning('Estimator does not exist: {}'.format(name))

    def assert_estimator_not_exist(self, name):
        if self.estimator_exists(name):
            raise UserWarning('Estimator exists: {}'.format(name))

    def tasks(self):
        """Yield tasks from the data store.

        Tasks are yielded as ``(estimator, task)`` pairs.
        """
        for estimator in self.estimators:
            for task in estimator.tasks:
                yield estimator, task

    def get_task(self, id):
        """Retrieve the task of the given ID.

        Return an ``(estimator, task)`` pair.
        """
        self.assert_task_exist(id)
        return [(e, t) for e, t in self.tasks() if t.id == id][0]

    def task_exists(self, id):
        """Return whether the task of the given id exists in the data store."""
        return any(t.id == id for e, t in self.tasks())

    def assert_task_exist(self, id):
        if not self.task_exists(id):
            raise UserWarning('Task does not exist: {}'.format(id))

    def assert_task_not_exist(self, id):
        if self.task_exists(id):
            raise UserWarning('Task exists: {}'.format(id))
