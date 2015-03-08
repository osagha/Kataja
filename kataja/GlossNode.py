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

from kataja.Node import Node
from kataja.globals import GLOSS_EDGE, GLOSS_NODE
from kataja.singletons import ctrl


color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class GlossNode(Node):
    """
    Node to display translation of a constituent
    """
    width = 20
    height = 20
    default_edge_type = GLOSS_EDGE
    node_type = GLOSS_NODE

    def __init__(self, text=''):
        Node.__init__(self)
        self.label = text


    def after_init(self):
        print("GlossNode after_init called")
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()

    @property
    def hosts(self):
        """


        :return:
        """
        return self.get_parents(edge_type=GLOSS_EDGE)


    @property
    def label(self):
        return self.saved.label

    @label.setter
    def label(self, value):
        for host in self.hosts:
            host.gloss = value
        self.saved.label = value
        self._inode_changed = True


    @property
    def text(self):
        return self.saved.label

    @text.setter
    def text(self, value):
        for host in self.hosts:
            host.gloss = value
        self.saved.label = value
        self._inode_changed = True

    def update_colors(self):
        """
        Deprecated for now? Does nothing, overrides, but doesn't call Node's update_colors.
        """
        pass
        # self.color = colors.drawing2
        # if self._label_complex:
        # self._label_complex.setDefaultTextColor(colors.drawing2)

    def __str__(self):
        return 'gloss: %s' % self.text

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        painter.setPen(self.contextual_color())
        if ctrl.pressed == self or self._hovering or ctrl.is_selected(self) or True:
            painter.drawRoundedRect(self.inner_rect, 5, 5)

        # x,y,z = self.current_position
        # w2 = self.width/2.0
        # painter.setPen(self.contextual_color())
        # painter.drawEllipse(-w2, -w2, w2 + w2, w2 + w2)


    def update_label(self):
        """

        :return:
        """
        Node.update_label(self)
        self._label_complex.show()
        print(self.opacity())
