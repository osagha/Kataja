# coding=utf-8
"""
GlossNode is a Node to display translation or explanation of a constituent
"""
#############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from kataja.singletons import qt_prefs
from kataja.Node import Node
from kataja.globals import GLOSS_EDGE, GLOSS_NODE


color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class GlossNode(Node):
    """
    Node to display translation of a constituent
    """
    width = 20
    height = 20
    default_edge_type = GLOSS_EDGE
    node_type = GLOSS_NODE

    def __init__(self, host=None, restoring=False):
        Node.__init__(self)
        self.saved.host = host
        if not restoring:
            self.update_label()
            self.update_bounding_rect()
            self.update_visibility()

    @property
    def host(self):
        return self.saved.host

    @host.setter
    def host(self, value):
        self.saved.host = value

    def update_colors(self):
        """
        Deprecated for now? Does nothing, overrides, but doesn't call Node's update_colors.
        """
        pass
        # self.color = colors.drawing2
        # if self._label_complex:
        #    self._label_complex.setDefaultTextColor(colors.drawing2)

    def __str__(self):
        if self.host:
            return '%s, gloss for %s' % (self.host.gloss, self.host)
        else:
            return 'orphaned gloss node'

    def get_html_for_label(self):
        """ This should be overridden if there are alternative displays for label """

        if self.host:
            return self.host.gloss
        else:
            return ''