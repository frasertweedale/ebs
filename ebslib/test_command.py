# This file is part of ebs
# Copyright (C) 2012 Benon Technologies Pty Ltd
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

import argparse
import datetime
import os
import re
import tempfile
import unittest

from . import command
from . import store
from . import estimator
from . import task


class CommandTestCase(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self._tmp = path
        self._store = store.Store(path)

    def tearDown(self):
        del self._store
        os.unlink(self._tmp)
        del self._tmp

    def run_command(self, args):
        name = self._command.__name__.lower()
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        self._command.add_parser(subparsers)
        args = parser.parse_args([name, '--store', self._tmp] + args)
        return args.command(args, parser, {name: self._command}, [])()


class AddEstimatorTestCase(CommandTestCase):
    _command = command.AddEstimator

    def test_add_estimator(self):
        name = 'JoeBloggs@example.com'
        self.assertFalse(self._store.estimator_exists(name))
        del self._store.data  # purge
        self.run_command(['--name', name])
        self.assertTrue(self._store.estimator_exists(name))
        with self.assertRaisesRegexp(
            UserWarning,
            r'exists.*\b{}\b'.format(re.escape(name))
        ):
            self.run_command(['--name', name])


class AddEventTestCase(CommandTestCase):
    _command = command.AddEvent

    def setUp(self):
        super(AddEventTestCase, self).setUp()
        with self._store as store:
            store.estimators.append(
                estimator.Estimator(name='JoeBloggs@example.com'))

    def test_add_event(self):
        name = 'JoeBloggs@example.com'
        today = datetime.date.today()
        datestr = '{}-{:02}-{:02}'.format(today.year, today.month, today.day)
        self.assertTrue(self._store.estimator_exists(name))
        del self._store.data  # purge data
        self.run_command([
            '--estimator', name,
            '--date', datestr,
            '--cost', '2.5',
            '--desc', 'Leave'
        ])
        self.assertEqual(
            self._store.get_estimator(name).events,
            [task.Event(date=today, cost=2.5, description='Leave')]
        )


class RmTaskTestCase(CommandTestCase):
    _command = command.RmTask

    def setUp(self):
        super(RmTaskTestCase, self).setUp()
        with self._store as store:
            store.estimators.append(
                estimator.Estimator(
                    name='JoeBloggs@example.com',
                    tasks=[task.Task(id='foo'), task.Task(id='bar')]
                )
            )
        del self._store.data  # guarantee clean store

    def test_set_up(self):
        """Ensure the test environment is correct."""
        self.assertEqual(
            self._store.get_estimator('JoeBloggs@example.com').tasks,
            [task.Task(id='foo'), task.Task(id='bar')]
        )

    def test_rm_existing_task(self):
        """Test task removal."""
        self.run_command(['--id', 'foo'])
        est = self._store.get_estimator('JoeBloggs@example.com')
        self.assertEqual(len(est.tasks), 1)
        self.assertEqual(est.tasks, [task.Task(id='bar')])

    def test_rm_nonexistant_task(self):
        """Test attempted removal of a nonexistant task."""
        est = self._store.get_estimator('JoeBloggs@example.com')
        before = list(est.tasks)
        self.run_command(['--id', 'quux'])
        del self._store.data  # purge data
        after = list(est.tasks)
        self.assertEqual(before, after)
