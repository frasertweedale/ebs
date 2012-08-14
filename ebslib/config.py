# This file is part of ebs
# Copyright (C) 2011 Benon Technologies Pty Ltd
# Copyright (C) 2011, 2012 Fraser Tweedale
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

import re

import clilib


class Config(clilib.Config):
    """ebs configuration"""

    @staticmethod
    def check_section(section):
        """Checks that the given section is valid.

        Return the given section if it is valid, otherwise raise
        ``UserWarning``.
        """
        if section in ['core', 'alias', 'sync'] \
                or re.match(r'server\.\w+', section):
            return section
        raise UserWarning('invalid section: {}'.format(section))
