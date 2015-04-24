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

from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


NO_ALIGN = 0
LEFT = 1
RIGHT = 2


class Equidistant3dTree(BaseVisualization):
    """

    """
    name = 'Equidistant 3d-net'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = False


    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            self.forest.vis_data = {'name': self.__class__.name}
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.use_fixed_position = False
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        node.dyn_y = True
        node.dyn_x = True
        node.dyn_z = True
        x, y, z = node.current_position
        node.current_position = (x, y, z + (random.random() * 10) - 5)


    def calculate_movement_o(self, node):
        # @time_me
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0

        node_x, node_y, node_z = node.current_position
        for other in self.forest.visible_nodes():
            other_x, other_y, other_z = other.current_position
            if other is node:
                continue
            dist_x = int(node_x - other_x)
            dist_y = int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist and dist < 100:
                l = (other.force / (dist * dist))
                xvel += dist_x * l
                yvel += dist_y * l

        for i, edge in enumerate(node.edges_up):
            if edge.is_visible():
                if edge.alignment == LEFT:
                    target_d_x = -30
                else:
                    target_d_x = 30
                target_d_y = 15
                start_x, start_y, start_z = edge.start_point
                end_x, end_y, end_z = edge.end_point
                d_x = end_x - start_x
                d_y = end_y - start_y
                rd_x = target_d_x - d_x
                rd_y = target_d_y - d_y
                xvel += rd_x * edge.pull / ((i + 1) * (i + 1))  # first branch has strongest pull
                yvel += rd_y * edge.pull  # / ((i + 1) * (i + 1))
            else:
                print('hidden edge ', edge)

        return xvel, yvel, 0


    def calculate_movement(self, node):
        # @time_me
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        zvel = 0.0
        node_x, node_y, node_z = node.current_position
        for other in self.forest.visible_nodes():
            other_x, other_y, other_z = other.current_position
            if other is node:
                continue
            dist_x = int(node_x - other_x)
            dist_y = int(node_y - other_y)
            dist_z = int(node_z - other_z)
            dist = math.pow(dist_x * dist_x + dist_y * dist_y + dist_z * dist_z, 0.3333333)
            if dist and dist < 1000:  # sqrt(dist) < 100
                l = other.force / (dist * dist * dist)
                xvel += dist_x * l
                yvel += dist_y * l
                zvel += dist_z * l
        # print 'before:', (xvel,yvel,zvel)

        # Now subtract all forces pulling items together.
        for edge in node.edges_up + node.edges_down:
            if edge.is_visible():
                bsx, bsy, bsz = edge.start_point
                bdx, bdy, bdz = edge.end_point
                if edge.start is node:
                    bx, by, bz = bdx - bsx, bdy - bsy, bdz - bsz
                else:
                    bx, by, bz = bsx - bdx, bsy - bdy, bsz - bdz
                dist = math.sqrt(bx * bx + by * by + bz * bz)
                if dist > 300:
                    # print(dist, edge)
                    # raise hell
                    pass
                if dist > 15:
                    fx = (bx / dist) * (dist - 30) * 0.2
                    fy = (by / dist) * (dist - 30) * 0.2
                    fz = (bz / dist) * (dist - 30) * 0.2
                    # print dist, fx, fy, fz, bx/dist, by/dist, bz/dist
                    xvel += fx
                    yvel += fy
                    zvel += fz
                    # elif dist < 20:
                    # xvel -= bx
                    # yvel -= by
                    # zvel -= bz
            else:
                print('hidden edge ', edge)

        # pull to center (0, 0)
        xvel += node_x * -0.002
        yvel += node_y * -0.002

        if not node.dyn_x:
            xvel = 0
        if not node.dyn_y:
            yvel = 0
        if not node.dyn_z:
            zvel = 0

        # print 'after:', (xvel, yvel, zvel)
        return xvel, yvel, zvel
