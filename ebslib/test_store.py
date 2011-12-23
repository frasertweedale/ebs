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

import datetime
import tempfile
import os
import unittest

from . import task
from . import estimator
from . import store


_estimators = [
    estimator.Estimator.from_dict(e) for e in
    {
        'name': 'Bob',
        'tasks': [
            {'id': 1, 'estimate': 4, 'description': 'Task 3'},
            {'estimate': 2, 'actual': 3, 'description': 'Task 4'},
        ],
        'events': [
            {'date': datetime.date.today(), 'cost': 2, 'description': 'Bar'}
        ]
    },
    {
        'name': 'Jane',
        'tasks': [
            {'estimate': 10, 'description': 'Task 1'},
            {'estimate': 20, 'actual': 25, 'description': 'Task 2'},
        ],
    },
]
_holidays = [datetime.date(2012, 1, 1)]
_data = {'estimators': _estimators, 'holidays': _holidays}


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        with open(path, 'w') as fp:
            store.write(fp, _data)
        self._tmp = path
        self._store = store.Store(path)

    def tearDown(self):
        del self._store
        os.unlink(self._tmp)
        del self._tmp

    def test_write_and_read(self):
        """Verify that data is written out and read back correctly."""
        with tempfile.TemporaryFile() as fp:
            store.write(fp, _data)
            fp.seek(0)
            self.assertEqual(_data, store.read(fp))

    def test_get_task(self):
        _estimator, _task = self._store.get_task(1)
        self.assertEqual(
            _task,
            task.Task(**{'id': 1, 'estimate': 4, 'description': 'Task 3'})
        )
        self.assertEqual(_estimator.name, 'Bob')

    def test_get_holidays(self):
        self.assertEqual(
            self._store.holidays,
            _holidays
        )
