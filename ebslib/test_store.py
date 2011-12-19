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
import tempfile
import unittest

from . import estimator
from . import store


_data = [
    {
        'name': 'Bob',
        'tasks': [
            {'estimate': 4, 'description': 'Task 3'},
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


class StoreTestCase(unittest.TestCase):
    def test_write_and_read(self):
        data = [estimator.Estimator.from_dict(e) for e in _data]
        with tempfile.TemporaryFile() as fp:
            store.write(fp, data)
            fp.seek(0)
            self.assertEqual(data, store.read(fp))
