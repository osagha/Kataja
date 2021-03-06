# -*- coding: UTF-8 -*-
# ############################################################################
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
# ############################################################################


import math

import kataja.globals as g
from kataja.Visualization import BaseVisualization
from kataja.singletons import prefs
from kataja.Shapes import direction_multiplier


def border_distance(n1x, n1y, n1w2, n1h2, n2x, n2y, n2w2, n2h2):
    dx, dy = n2x - n1x, n2y - n1y

    if dx == 0:
        if abs(dy) < n2h2 + n1h2:
            return 1, 0, 1, True
        elif dy > 0:
            d = dy - n2h2 - n1h2
        else:
            d = dy + n2h2 + n2h2
        return d, 0, d, False
    elif dy == 0:
        if abs(dx) < n2w2 + n1w2:
            return 1, 1, 0, True
        elif dx > 0:
            d = dx - n2w2 - n1w2
        else:
            d = dx + n2w2 + n2w2
        return d, d, 0, False
    else:
        ratio = float(dx) / dy

    if dx > 0:
        e1x = n1w2
        p1y = n1w2 / ratio
        e2x = -n2w2
        p2y = -n2w2 / ratio
    else:
        e1x = -n1w2
        p1y = -n1w2 / ratio
        e2x = n2w2
        p2y = n2w2 / ratio

    if dy > 0:
        e1y = n1h2
        p1x = n1h2 * ratio
        e2y = -n2h2
        p2x = -n2h2 * ratio
    else:
        e1y = -n1h2
        p1x = -n1h2 * ratio
        e2y = n2h2
        p2x = n2h2 * ratio

    # first rect
    if abs(p1x) > abs(e1x):
        p1x = e1x
    else:
        p1y = e1y
    # second rect
    if abs(p2x) > abs(e2x):
        p2x = e2x
    else:
        p2y = e2y

    # overlap detection
    if abs(dx) < abs(p1x) + abs(p2x) or abs(dy) < abs(p1y) + abs(p2y):
        # all overlaps are push equally hard
        d = max(1, math.hypot(dx, dy))
        return 1, dx / d, dy / d, True
    else:
        fdx, fdy = n2x + p2x - (n1x + p1x), n2y + p2y - (n1y + p1y)
        d = max(1, math.hypot(fdx, fdy))
        return d, fdx, fdy, False


class AsymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Asymmetric Elastic Tree'
    hide_edges_if_nodes_overlap = False

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None

    def calculate_movement(self, node):
        """ Basic dynamic force net, but instead of computing distances from center of gravity of
         each object (which assumes round nodes, compute distances starting from the boundary
         rect. The forces pulling tree together use the magnets that mark edge connection points
         as basis of their distance calculation.

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        node_x, node_y = node.centered_scene_position  # @UnusedVariable
        node_br = node.boundingRect()
        nw2, nh2 = node_br.width() / 2.0, node_br.height() / 2.0

        for other in self.forest.visible_nodes():
            other_br = other.boundingRect()
            if other is node:
                continue
            elif other.locked_to_node is node or node.locked_to_node is other:
                continue

            other_x, other_y = other.centered_scene_position  # @UnusedVariable

            d, dx, dy, overlap = border_distance(node_x, node_y, nw2, nh2, other_x, other_y,
                                                 other_br.width() / 2,
                                                 other_br.height() / 2)
            if d == 0:
                continue
            l = -3.0 / (d * d)
            xvel += dx * l
            yvel += dy * l
        # Now subtract all forces pulling items together.
        for edge in node.edges_down:
            if not edge.is_visible():
                continue
            elif edge.end.locked_to_node is node:
                continue
            edge_n, edge_count = edge.edge_index()
            target_d_x = direction_multiplier(edge_n, edge_count) * prefs.edge_width
            target_d_y = -15
            start_x, start_y = edge.start_point  # @UnusedVariable
            end_x, end_y = edge.end_point  # @UnusedVariable
            d_x = start_x - end_x
            d_y = start_y - end_y
            #print(start_x, end_x, d_x)
            rd_x = d_x - target_d_x
            rd_y = d_y - target_d_y
            xvel -= rd_x * edge.pull * 0.3
            yvel -= rd_y * edge.pull * 0.3

        for i, edge in enumerate(node.edges_up):
            if not edge.is_visible():
                continue
            elif node.locked_to_node is edge.end:
                continue
            edge_n, edge_count = edge.edge_index()
            target_d_x = direction_multiplier(edge_n, edge_count) * prefs.edge_width
            target_d_y = 15
            start_x, start_y = edge.start_point  # @UnusedVariable
            end_x, end_y = edge.end_point  # @UnusedVariable
            d_x = end_x - start_x
            d_y = end_y - start_y
            #print(start_x, end_x, d_x)
            rd_x = d_x - target_d_x
            rd_y = d_y - target_d_y
            xvel -= rd_x * edge.pull * 0.6 / ((i + 1) * (i + 1))  # first branch has strongest pull
            yvel -= rd_y * edge.pull * 0.6 / ((i + 1) * (i + 1))

        # pull to center (0, 0)
        # let's remove this from node, and put it to trees instead
        #xvel += node_x * -0.008
        #yvel += node_y * -0.008

        if not node.physics_x:
            xvel = 0
        if not node.physics_y:
            yvel = 0
        return xvel, yvel, 0

    def calculate_tree_movement(self):
        """ Make trees to maintain some distance from each other
        :return:
        """
        pass

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
