# This file is part of ebs
# Copyright (C) 2011 Benon Technologies Pty Ltd, Fraser Tweedale
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

from __future__ import unicode_literals

import argparse
import datetime
import itertools
import re
import textwrap

from . import config as _config
from . import task as _task
from . import estimator as _estimator
from . import date as _date
from . import store as _store

conf = _config.Config.get_config('~/.ebsrc')


def date(s):
    match = re.match(r'(\d{4})-(\d\d)-(\d\d)$', s)
    if not match:
        raise argparse.ArgumentTypeError('Date must be in format: YYYY-MM-DD')
    try:
        return datetime.date(*map(int, match.group(1, 2, 3)))
    except ValueError as e:
        raise argparse.ArgumentTypeError(e.message)


class Command(object):
    """A command object.

    Provides arguments.  Does what it does using __call__.
    """

    args = []
    """
    An array of (args, kwargs) tuples that will be used as arguments to
    ArgumentParser.add_argument().
    """

    @classmethod
    def help(cls):
        return textwrap.dedent(filter(None, cls.__doc__.splitlines())[0])

    @classmethod
    def epilog(cls):
        return textwrap.dedent('\n\n'.join(cls.__doc__.split('\n\n')[1:]))

    def __init__(self, args, parser, commands, aliases):
        """
        args: an argparse.Namespace
        parser: the argparse.ArgumentParser
        commands: a dict of all Command classes keyed by __name__.lower()
        aliases: a dict of aliases keyed by alias
        """
        self._args = args
        self._parser = parser
        self._commands = commands
        self._aliases = aliases


class Config(Command):
    """Show or update configuration."""
    args = Command.args + [
        lambda x: x.add_argument('--list', '-l', action='store_true',
            help='list all configuration options'),
        lambda x: x.add_argument('name', nargs='?',
            help='name of option to show, set or remove'),
        lambda x: x.add_argument('--remove', action='store_true',
            help='remove the specified option'),
        lambda x: x.add_argument('value', nargs='?',
            help='set value of given option'),
    ]

    def __call__(self):
        args = self._args
        if args.list:
            for section in conf.sections():
                for option, value in conf.items(section):
                    print '{}={}'.format('.'.join((section, option)), value)
        elif not args.name:
            raise UserWarning('No configuration option given.')
        else:
            try:
                section, option = args.name.rsplit('.', 1)
            except ValueError:
                raise UserWarning('Invalid configuration option.')
            if not section or not option:
                raise UserWarning('Invalid configuration option.')

            if args.remove:
                # remove the option
                conf.remove_option(section, option)
                if not conf.items(section):
                    conf.remove_section(section)
                conf.write()
            elif args.value:
                # set new value
                if not conf.has_section(section):
                    conf.add_section(section)
                oldvalue = conf.get(section, option) \
                    if conf.has_option(section, option) else None
                conf.set(section, option, args.value)
                conf.write()
                print '{}: {} => {}'.format(args.name, oldvalue, args.value)
            else:
                curvalue = conf.get(section, option)
                print '{}: {}'.format(args.name, curvalue)


class Help(Command):
    """Show help."""
    args = Command.args + [
        lambda x: x.add_argument('subcommand', metavar='SUBCOMMAND', nargs='?',
            help='show help for subcommand')
    ]

    def __call__(self):
        if not self._args.subcommand:
            self._parser.parse_args(['--help'])
        else:
            if self._args.subcommand in self._aliases:
                print "'{}': alias for {}".format(
                    self._args.subcommand,
                    self._aliases[self._args.subcommand]
                )
            elif self._args.subcommand not in self._commands:
                print "unknown subcommand: '{}'".format(self._args.subcommand)
            else:
                self._parser.parse_args([self._args.subcommand, '--help'])


class EBSCommand(Command):
    args = Command.args + [
        lambda x: x.add_argument('--store', default='~/.ebs',
            help='Path to datastore'),
    ]

    def __call__(self):
        with _store.Store(self._args.store) as store:
            self._store = store
            self._run()
            del self._store


class AddEstimator(EBSCommand):
    """Add an estimator."""
    args = EBSCommand.args + [
        lambda x: x.add_argument('--name', required=True,
            help='Name of new estimator'),
    ]

    def _run(self):
        self._store.assert_estimator_not_exist(self._args.name)
        self._store.data.append(_estimator.Estimator(name=self._args.name))


class AddTask(EBSCommand):
    """Add a task."""
    args = EBSCommand.args + [
        lambda x: x.add_argument('--estimator', metavar='NAME', required=True,
            help='Estimator (assignee) of the task.'),
        lambda x: x.add_argument('--id', required=True,
            help='Unique identifier for task.'),
        lambda x: x.add_argument('--description', metavar='DESC',
            help='Description of task.'),
        lambda x: x.add_argument('--priority', type=int,
            help='Priority of the task.'),
        lambda x: x.add_argument('--estimate', metavar='COST',
            type=float, required=True,
            help='Estimated cost of the task.'),
        lambda x: x.add_argument('--actual', metavar='COST',
            type=float, default=0,
            help='Actual cost of the task.'),
        lambda x: x.add_argument('--date', type=date,
            help='Date of the estimate'),
    ]
    _attrs = ('id', 'description', 'priority', 'estimate', 'actual', 'date')

    def _run(self):
        self._store.assert_task_not_exist(self._args.id)
        self._store.assert_estimator_exist(self._args.estimator)
        task = _task.Task(
            **{attr: getattr(self._args, attr) for attr in self._attrs})
        self._store.get_estimator(self._args.estimator).tasks.append(task)


class Estimate(EBSCommand):
    """Perform an estimation using Monte Carlo simulations."""
    def _run(self):
        task_hours_per_day = float(conf.get('core', 'task_hours_per_day'))
        event_hours_per_day = float(conf.get('core', 'event_hours_per_day'))
        today = datetime.date.today()
        for e in self._store.estimators():
            future_sums = (sum(ests) for ests in e.simulate_futures())
            future_slice = (itertools.islice(future_sums, 100))
            future_dates = (
                _date.ship_date(
                    task_hours=h,
                    task_hours_per_day=task_hours_per_day,
                    event_hours=e.future_event_cost,
                    event_hours_per_day=event_hours_per_day,
                    start_date=today
                )
                for h in future_slice
            )
            sorted_futures = sorted(future_dates)
            print e.name
            for i in range(9, 100, 10):
                print '  {:2}% : {}'.format(i, sorted_futures[i])


# the list got too long; metaprogram it ^_^
commands = filter(
    lambda x: type(x) == type                # is a class \
        and issubclass(x, Command)           # is a Command \
        and x not in [Command, EBSCommand],  # not abstract
    locals().viewvalues()
)
