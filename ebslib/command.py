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


class AddEvent(EBSCommand):
    """Add an event."""
    args = EBSCommand.args + [
        lambda x: x.add_argument('--estimator', metavar='NAME', required=True,
            help='Estimator occupied by the event.'),
        lambda x: x.add_argument('--date', required=True, type=date,
            help='Date of the event.'),
        lambda x: x.add_argument('--cost', metavar='HOURS',
            type=float, required=True,
            help='Cost of the event.'),
        lambda x: x.add_argument('--description', metavar='DESC',
            help='Description of task.'),
    ]
    _attrs = ('date', 'cost', 'description')

    def _run(self):
        hpd = float(conf.get('core', 'hours_per_day'))
        if self._args.cost > hpd:
            raise UserWarning('Event cannot have cost greater than one day.')
        self._store.assert_estimator_exist(self._args.estimator)
        event = _task.Event(
            **{attr: getattr(self._args, attr) for attr in self._attrs})
        self._store.get_estimator(self._args.estimator).events.append(event)


class AddHoliday(EBSCommand):
    """Add a holiday."""
    args = EBSCommand.args + [
        lambda x: x.add_argument('--date', required=True, type=date,
            help='Date of the holiday.'),
    ]

    def _run(self):
        if self._args.date not in self._store.holidays:
            self._store.holidays.append(self._args.date)


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
        lambda x: x.add_argument('--estimate', metavar='HOURS',
            type=float, required=True,
            help='Estimated cost of the task.'),
        lambda x: x.add_argument('--actual', metavar='HOURS',
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
    args = EBSCommand.args + [
        lambda x: x.add_argument('--exponent', metavar='N', type=int,
            default=2,
            help='Perform 10^N rounds of simulation (n >=2)'),
    ]

    def _run(self):
        exp = self._args.exponent if self._args.exponent >= 2 else 2
        hpd = float(conf.get('core', 'hours_per_day'))
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        for e in self._store.estimators:
            future_sums = (sum(ests) for ests in e.simulate_futures())
            future_slice = (itertools.islice(future_sums, 10 ** exp))
            future_dates = (
                _date.ship_date(
                    hours=h, hours_per_day=hpd, start_date=today,
                    events=list(e.get_events(start=tomorrow))
                )
                for h in future_slice
            )
            print e.name
            try:
                sorted_futures = \
                    sorted(future_dates, key=lambda x: (x[0], -x[1]))
                for i in xrange(
                    10 ** (exp - 1) - 1,
                    10 ** exp,
                    10 ** (exp - 1)
                ):
                    print '  {:2}% : {}'.format(
                        (i + 1) / 10 ** (exp - 2) - 1, sorted_futures[i][0]
                    )
            except _estimator.NoHistoryError as e:
                print '  ' + e.message


class LsEvent(EBSCommand):
    """List events by estimator."""
    def _run(self):
        for e in self._store.estimators:
            print e.name
            events = e.get_events(start=datetime.date.today())
            n = 0
            for event in sorted(events, key=lambda x: x.date):
                n += 1
                print '  {} {:4.2}h {}'.format(
                    event.date,
                    event.cost,
                    '({})'.format(event.description) if event.description \
                        else ''
                )
            if not n:
                print '  No events'


class LsHoliday(EBSCommand):
    """List holidays."""
    def _run(self):
        for date in sorted(self._store.holidays):
            print date


class RmEstimator(EBSCommand):
    """Remove an estimator."""

    args = EBSCommand.args + [
        lambda x: x.add_argument('--name', required=True,
            help='name of the estimator to remove'),
    ]

    def _run(self):
        estimator = self._store.get_estimator(self._args.name)
        self._store.estimators.remove(estimator)
        print "Removed estimator '{}'.".format(estimator.name)


class RmHoliday(EBSCommand):
    """Remove a holiday."""
    args = EBSCommand.args + [
        lambda x: x.add_argument('--date', required=True, type=date,
            help='Date of the holiday.'),
    ]

    def _run(self):
        if self._args.date in self._store.holidays:
            self._store.holidays.remove(self._args.date)


class Stats(EBSCommand):
    """Calculate velocity statistics for each estimator."""
    def _run(self):
        for e in self._store.estimators:
            print e.name
            print (
                '  n: {}, min: {:.2}, max: {:.2}, mean: {:.2}, stddev: {:.2}'
                .format(
                    len(e.velocities()),
                    e.min_velocity(),
                    e.max_velocity(),
                    e.mean_velocity(),
                    e.stddev_velocity()
                )
            )


class Sync(EBSCommand):
    """Sync task and time from Bugzilla."""
    def _parse_dict(self, string):
        # TODO: break out into util module?
        pairs = string.split(',')
        items = ((x.strip() for x in pair.split('=')) for pair in pairs)
        return dict(items)

    def _run(self):
        sync_conf = dict(conf.items('sync'))
        _search_args = self._parse_dict(sync_conf['search_args'])

        # import bugzillatools modules
        import bzlib.bugzilla
        import bzlib.bug

        kwargs = {x: sync_conf[x] for x in ('url', 'user', 'password')}
        bz = bzlib.bugzilla.Bugzilla(**kwargs)

        bugs = bzlib.bug.Bug.search(bz, **_search_args)
        for bug in sorted(bugs, key=lambda x: x.id):
            self._add_or_update_task(bug)

    def _add_or_update_task(self, bug):
        if self._store.estimator_exists(bug.data['assigned_to']):
            if self._store.task_exists(bug.id):
                self._update_task(bug)
            else:
                self._add_task(bug)
        else:
            print "SKIP   {} : no estimator for assignee '{}'.".format(
                bug.id, bug.data['assigned_to'])

    def _add_task(self, bug):
        task = _task.Task(**dict(self._extract_task_data(bug)))
        self._store.get_estimator(bug.data['assigned_to']).tasks.append(task)
        print "ADD    {} : add task: {}".format(bug.id, bug.data['summary'])

    def _update_task(self, bug):
        old_estimator, task = self._store.get_task(bug.id)
        estimator = self._store.get_estimator(bug.data['assigned_to'])
        if old_estimator != estimator:
            # move task to new estimator
            old_estimator.tasks.remove(task)
            estimator.tasks.add(task)
            print "MOVE   {} : reassigned from '{}' to '{}'.".format(
                old_estimator.name, estimator.name)
        diff = False
        for k, v in self._extract_task_data(bug):
            oldv = getattr(task, k)
            if oldv != v:
                diff = True
                print "UPDATE {} : {}: {} -> {}".format(bug.id, k, oldv, v)
                setattr(task, k, v)
        if not diff:
            print "NODIFF {} : task unchanged.".format(bug.id)

    def _extract_task_data(self, bug):
        """Generate pairs of task data extracted from the bug."""
        yield 'id', bug.id
        yield 'description', bug.data['summary']
        yield 'estimate', bug.data['estimated_time']
        yield 'actual', 0 if bug.is_open() else bug.actual_time(),
        # TODO: extract date of estimate from history
        # TODO: extract priority


# the list got too long; metaprogram it ^_^
commands = filter(
    lambda x: type(x) == type                # is a class \
        and issubclass(x, Command)           # is a Command \
        and x not in [Command, EBSCommand],  # not abstract
    locals().viewvalues()
)
