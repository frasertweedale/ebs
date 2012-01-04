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
import os
import re
import tempfile
import unittest

from . import command
from . import store


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
