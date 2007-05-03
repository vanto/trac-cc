#
# Copyright (C) 2005 Tammo van Lessen <tvanlessen@gmail.com>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Tammo van Lessen <tvanlessen@gmail.com>
from setuptools import setup

from traccc import __version__ as VERSION

setup(
  name='TracCC',
  version=VERSION,
  packages=['traccc'],
  package_data={'traccc' : ['htdocs/*.css', 'htdocs/*.gif', 'templates/*.cs']},
  author = 'Tammo van Lessen',
  description = 'A plugin to integrate Cruise Control into Trac',
  url = 'http://oss.werkbold.de/trac-cc',
  license = 'GPL',
  entry_points={'trac.plugins': 'traccc = traccc'}
)
