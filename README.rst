This program implements "evidence based scheduling" `as described by
Joel Spolsky <http://www.joelonsoftware.com/items/2007/10/26.html>`_.

Tasks and their scheduled and actual durations can be manually
entered or can be read from `Bugzilla <http://www.bugzilla.org>`_
(requires `bugzillatools <https://github.com/frasertweedale/bugzillatools>`_).


Commands
--------

:addestimator:        Add an estimator.
:addevent:            Add an event.
:addholiday:          Add a holiday.
:addtask:             Add a task.
:config:              Show or update configuration.
:estimate:            Perform an estimation using Monte Carlo simulations.
:help:                Show help.
:lsevent:             List events by estimator.
:lsholiday:           List holidays.
:lstask:              List tasks.
:rmestimator:         Remove an estimator.
:rmholiday:           Remove a holiday.
:rmtask:              Remove a task.
:stats:               Calculate velocity statistics for each estimator.
:sync:                Sync task data from Bugzilla.


Installation
------------

::

  # from source
  python setup.py install           # as superuser
    -or-
  python setup.py install --user    # user site-packages installation

The ``bin/`` directory in your user base directory will need to appear
on the ``PATH`` if installing to user site-packages.  This directory is
system dependent; see `PEP 370`__.

__ http://www.python.org/dev/peps/pep-0370/
