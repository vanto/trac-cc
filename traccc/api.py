#
# Copyright (C) 2007 Tammo van Lessen <tvanlessen@gmail.com>
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

from trac.core import *

class ICruiseControlLogRenderer(Interface):
    def render(element):
        """Renders a cruisecontrol log section to HTML."""

    def get_supported_elements():
        """Returns a list of log elements supported by this renderer."""

    def get_priority():
        """Returns the priority of the renderer. If there are more than one
        renderers are registered for a particular log element, the renderer
        with the highest priority will be used."""
