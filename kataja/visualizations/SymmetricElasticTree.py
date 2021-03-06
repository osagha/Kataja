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
import random

import kataja.globals as g
from kataja.Visualization import BaseVisualization


class SymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic directionless net'
    hide_edges_if_nodes_overlap = False

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self.use_gravity = False

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.reset_nodes()
        self.validate_node_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        node.update_label()
        node.update_visibility()
        node.physics_x = True
        node.physics_y = True

    def calculate_movement(self, node):
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        node_x, node_y = node.centered_position  # @UnusedVariable
        for other in self.forest.visible_nodes():
            if other is node:
                continue
            elif other.locked_to_node is node or node.locked_to_node is other:
                continue
            other_x, other_y = other.centered_position  # @UnusedVariable
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            safe_zone = (other.width + node.width) / 2
            dist = math.hypot(dist_x, dist_y)
            if dist == 0 or dist == safe_zone:
                continue
            required_dist = dist - safe_zone
            pushing_force = 500 / (required_dist * required_dist)
            pushing_force = min(0.6, pushing_force)

            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel += pushing_force * x_component
            yvel += pushing_force * y_component

        # Now subtract all forces pulling items together.
        for edge in node.edges_down:
            other = edge.end
            if other.locked_to_node is node:
                continue
            other_x, other_y = other.centered_position
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            safe_zone = (other.width + node.width) / 2
            pulling_force = (dist - safe_zone) * edge.pull * 0.4
            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel -= x_component * pulling_force
            yvel -= y_component * pulling_force

        for edge in node.edges_up:
            other = edge.start
            if node.locked_to_node is other:
                continue
            other_x, other_y = other.centered_position
            dist_x, dist_y = (node_x - other_x, node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            safe_zone = (other.width + node.width) / 2
            pulling_force = (dist - safe_zone) * edge.pull * 0.4
            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel -= x_component * pulling_force
            yvel -= y_component * pulling_force

        # pull to center (0, 0)
        xvel += node_x * -0.003
        yvel += node_y * -0.003

        if not node.physics_x:
            xvel = 0
        if not node.physics_y:
            yvel = 0
        return xvel, yvel, 0
