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

from kataja.debug import vis
from kataja.singletons import prefs
from kataja.utils import caller
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.visualizations.Grid import Grid
import kataja.globals as g


class LeftFirstTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left. Each
    branch takes the space it needs, and may force next branch drawing to
    further down and right. """
    name = 'Left first tree'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        vis('preparing LeftFirstVisualization')
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self._indentation = 0
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            self.set_vis_data('rotation', 0)
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        if node.node_type == g.CONSTITUENT_NODE:
            node.dyn_x = False
            node.dyn_y = False
        else:
            node.dyn_x = True
            node.dyn_y = True

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating
        between different modes is triggered here. """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)

    # Recursively put nodes to their correct position in grid
    def _put_to_grid(self, grid, node, x, y, parent=None):
        if not self.should_we_draw(node, parent):
            return
        grid.set(x, y, node)
        children = list(node.get_visible_children())
        if not children:
            return
        x_shift = (len(children) // 2) * -2
        x_step = 2
        y_step = 2
        first = True
        nx = x + x_shift
        ny = y + y_step
        for child in children:
            if first:
                blocked = grid.get(nx, ny)
                if not blocked:
                    path = grid.pixelated_path(x, y, nx, ny)
                    blocked = grid.is_path_blocked(path)
                    if not blocked:
                        grid.fill_path(path)
                        self._put_to_grid(grid, child, nx, ny, parent=node)
                #assert not blocked
                first = False
                if len(children) > 2:
                    nx += x_step
                else:
                    nx += x_step * 2

            else:
                blocked = True
                grandchildren = list(child.get_visible_children())
                while blocked:
                    # is the right node position available?
                    blocked = grid.get(nx, ny)
                    if not blocked:
                        # is the path to the right node position available?
                        path = grid.pixelated_path(x, y, nx, ny)
                        blocked = grid.is_path_blocked(path)
                        if not blocked:
                            # is there room for the left child of this node
                            if grandchildren:
                                if len(grandchildren) == 1:
                                    child_pos_x, child_pos_y = nx, \
                                                               ny + y_step  #
                                                               #  middle
                                else:
                                    child_pos_x, child_pos_y = nx - x_step, \
                                                               ny + y_step  #
                                                               #  reach left
                                blocked = grid.get(child_pos_x, child_pos_y)
                                if not blocked:
                                    cpath = grid.pixelated_path(nx, ny,
                                                                child_pos_x,
                                                                child_pos_y)
                                    blocked = grid.is_path_blocked(cpath)
                    if blocked:
                        nx += x_step
                        ny += y_step
                grid.fill_path(path)
                self._put_to_grid(grid, child, nx, ny, parent=node)
                nx += x_step

    # @time_me
    def draw(self):
        """ Draws the tree to a table or a grid, much like latex qtree and
        then scales the grid to the scene. """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        merged_grid = Grid()
        self._indentation = 0
        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
            self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)
        for root in self.forest:
            grid = Grid()
            if root.node_type == g.CONSTITUENT_NODE:
                self._put_to_grid(grid, root, 0, 0)
                merged_grid.merge_grids(grid, extra_padding=2)
                # merged_grid = self._merge_grids(grid, merged_grid)

        offset_x = 0  # tree_w/-2
        y = 0
        # Actual drawing: set nodes to their places in scene
        if merged_grid:
            # merged_grid.ascii_dump()
            extra_width = [0] * merged_grid.width
        else:
            extra_width = [0]
        # if node is extra wide, then move all columns to right from that
        # point on
        # same for extra tall nodes. move everything down after that row

        all_nodes = set(self.forest.get_constituent_nodes())
        for y_i, row in enumerate(merged_grid):
            extra_height = 0
            prev_width = 0
            x = offset_x
            for x_i, node in enumerate(row):
                if node and getattr(node, 'node_type',
                                    '') == g.CONSTITUENT_NODE:
                    if not node.inner_rect:
                        node.update_bounding_rect()
                    height_spillover = node.inner_rect.bottom() - edge_height
                    if height_spillover > extra_height:
                        extra_height = math.ceil(
                            height_spillover / float(edge_height)) * edge_height
                    width_spillover = ((node.width + prev_width) / 2) - (
                    edge_width * 4)
                    if width_spillover > extra_width[x_i]:
                        extra_width[x_i] = math.ceil(
                            width_spillover / float(edge_width)) * edge_width
                    x += extra_width[x_i]
                    node.algo_position = (x, y, 0)
                    prev_width = node.width
                    if not node in all_nodes:
                        print(
                            'non-visible node included in visualization grid: ',
                            node)
                    else:
                        all_nodes.remove(node)
                else:
                    x += extra_width[x_i]
                x += edge_width
            y += edge_height + extra_height
        if all_nodes:
            vis('nodes left remaining: ', all_nodes)
