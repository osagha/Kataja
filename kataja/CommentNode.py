# coding=utf-8
"""
CommentNode is a non-functional node for freeform text
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
from kataja.globals import COMMENT_EDGE, COMMENT_NODE
from kataja.singletons import ctrl
from kataja.parser.INodes import ITextNode
from kataja.parser.LatexToINode import parse_field


color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class CommentNode(Node):
    """
    Node to display translation of a constituent
    """
    width = 20
    height = 20
    default_edge_type = COMMENT_EDGE
    node_type = COMMENT_NODE

    def __init__(self, text=''):
        Node.__init__(self)
        self.label = text


    def after_init(self):
        print("CommentNode after_init called")
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()
        ctrl.forest.store(self)

    @property
    def hosts(self):
        """


        :return:
        """
        return self.get_parents(edge_type=COMMENT_EDGE)


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
        return 'comment: %s' % self.text

    @property
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            if isinstance(self.label, ITextNode):
                self._inode = self.label
            else:
                self._inode = parse_field(self.label)
            print('comment node inode is: ', self._inode)
            self._inode_changed = False
        return self._inode