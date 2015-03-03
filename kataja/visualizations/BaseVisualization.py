# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic BaseVisualization tool ***
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

from kataja.singletons import prefs
from kataja.utils import caller
from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g

LEFT = 1
NO_ALIGN = 0
RIGHT = 2


class BaseVisualization:
    """ Base class for different 'drawTree' implementations """
    name = 'BaseVisualization base class'

    def __init__(self):
        """ This is called once when building Kataja. Set up properties for this kind of 
        visualization. vis_data can be used to store states of visualization: when restoring a visualization, vis_data is the only stored data that can be used. """
        self.forest = None
        self._directed = False
        self._hits = {}
        self._max_hits = {}

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = False
        self._hits = {}
        self._max_hits = {}
        self.forest.settings.bracket_style = g.NO_BRACKETS
        self.forest.settings.show_constituent_edges = True
        if reset:
            self.forest.vis_data = {'name': self.__class__.name}
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        node.update_label()
        if isinstance(node, ConstituentNode):
            node.update_visibility()
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            pass
        node.bind_y = False
        node.bind_x = False


    def draw(self):
        """ Subclasses implement this """
        pass


    # def reset(self):
    # """ Not sure if this should be used at all, it is confusing in its purpose """
    # #print '*** Reset visualization (base) ***'
    # if not self.forest:
    # return

    # for node in ctrl.scene.visible_nodes(self.forest):
    # node.reset()
    # node.update_label()
    # vis = node.is_visible()
    # node.update_visibility(show_edges = True, scope = 0)
    # if node.is_visible() != vis:
    # print 'V node hidden: ', node

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        pass

    def _count_occurences_of_node(self, root):
        self._hits = {}
        self._max_hits = {}
        for node in root:
            self._hits[node.save_key] = self._hits.get(node.save_key, 0) + 1
            self._max_hits[node.save_key] = self._hits[node.save_key]

    def _reduce_node_count(self, node):
        self._hits[node.save_key] = self._hits.get(node.save_key, 0) - 1

    def _is_last_node(self, node):
        return self._hits[node.save_key] == 0

    def _is_first_node(self, node):
        return self._hits[node.save_key] == self._max_hits[node.save_key] - 1

    def _mark_node_as_used(self, node):
        self._hits[node.save_key] = 0

    def _is_node_used_already(self, node):
        return self.hits[node.save_key] == 0


    def calculate_movement(self, node, alpha = 0.7):
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        node_x, node_y, node_z = node.current_position
        old_x, old_y, old_z = node.current_position
        # repulse
        for other in self.forest.visible_nodes():
            if other is node:
                continue
            other_x, other_y, other_z = other.current_position  # @UnusedVariable
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            #if dist > 50:
            #    continue
            if dist == 0:
                print("boing 1")
                node_x += 5
                continue
            safe_zone = (other.width + node.width) / 2
            if dist == safe_zone:
                continue
            if dist < safe_zone:
                required_dist = abs(dist - safe_zone)
                pushing_force = required_dist / (dist * dist * alpha)
                #pushing_force = min(random.random() * 60, pushing_force)

                node_x += pushing_force * dist_x
                node_y += pushing_force * dist_y

        # attract
        down = node.edges_down
        for edge in down:
            other = edge.end
            other_x, other_y, other_z = other.current_position
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                print("boing 2")
                node_x += 5
                continue
            safe_zone = (other.width + node.width) / 2
            required_dist = dist - safe_zone
            pulling_force = (required_dist * edge.pull * alpha) / dist
            node_x -= dist_x * pulling_force
            node_y -= dist_y * pulling_force

        up = node.edges_up
        for edge in up:
            other = edge.start
            other_x, other_y, other_z = other.current_position
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                print("boing 3")
                node_x += 5
                continue
            safe_zone = (other.width + node.width) / 2
            required_dist = dist - safe_zone
            pulling_force = (required_dist * edge.pull * alpha) / dist
            node_x -= dist_x * pulling_force
            node_y -= dist_y * pulling_force

        if not (up or down):
            # pull to center (0, 0)
            node_x += node_x * -0.009
            node_y += node_y * -0.009
        elif not down:
            node_y += node._gravity


        if node.bind_x:
            xvel = 0
        else:
            xvel = node_x - old_x
        if node.bind_y:
            yvel = 0
        else:
            yvel = node_y - old_y
        return xvel, yvel, 0


    # def calculateFeatureMovement(self, feat, node):
    # """ Create a cloud of features around the node """
    # xvel = 0.0
    # yvel = 0.0
    # pull=.24
    #     node_x,node_y,node_z=feat.current_position
    #     sx,sy,sz=node.current_position
    #     for item in ctrl.scene.visible_nodes(self.forest):
    #         item_x,item_y,iz=item.current_position
    #         dist_x=int(node_x-item_x)
    #         dist_y=int(node_y-item_y)
    #         dist=math.hypot(dist_x,dist_y)
    #         if dist and dist<100:
    #             l= item.force/(dist*dist)
    #             xvel+=dist_x*l
    #             yvel+=dist_y*l

    #     for item in node.features:
    #         if item is feat: continue
    #         item_x,item_y,iz=item.current_position
    #         dist_x=int(node_x-item_x)
    #         dist_y=int(node_y-item_y)
    #         dist=math.hypot(dist_x,dist_y)
    #         if dist and dist<100:
    #             l= (item.force*2)/(dist*dist)
    #             xvel+=dist_x*l
    #             yvel+=dist_y*l
    #     # gravity
    #     #yvel+=0.6

    #     # Now subtract node's pull.
    #     bx,by= sx-node_x, sy-node_y
    #     dist=math.hypot(bx,by)
    #     if dist>20:
    #         ang=math.atan2(by,bx)
    #         fx=math.cos(ang)*(dist-15)
    #         fy=math.sin(ang)*(dist-15)
    #         xvel+=fx*pull
    #         yvel+=fy*pull

    #     for b in feat.targets:
    #         bbx,bby,bbz=b.current_position
    #         edge_length_x,edge_length_y=bbx-node_x, bby-node_y
    #         xvel+=edge_length_x*pull*.2
    #         yvel+=edge_length_y*pull*.4
    #     return (xvel, yvel, 0)



    def should_we_draw(self, node, parent):
        """

        :param node:
        :param parent:
        :return:
        """
        if len(node.get_parents()) > 1:
            key = node.index
            if key in self.traces_to_draw:
                if parent.save_key != self.traces_to_draw[key]:
                    return False
        return True

    def show_edges_for(self, node):
        """ Allow visualizations to override edge visibility. Edges are downward constituent edges of given node.
        :param node: Node to check -- don't need to be used if the result is always the same.
        :return:
        """
        return True

    def _compute_traces_to_draw(self, rotator):
        """ This is complicated, but returns a dictionary that tells for each index key (used by chains) in which position at tree to draw the node. Positions are identified by key of their immediate parent: {'i': ConstituentNode394293, ...} """
        # highest row = index at tree
        # x = cannot be skipped, last instance of that trace
        # i/j/k = index key
        # rows = rotation
        # * = use this node

        # 2 3 7 9 13 15 16
        # i j i i k  j  k
        #       x    x  x
        # * *     *
        #   * *   *
        #     *   *  *
        #       * *  *
        #       *    *  *

        trace_dict = {}
        sorted_parents = []
        required_keys = set()
        for tree in self.forest:
            sortable_parents = []
            ltree = self.forest.list_nodes_once(tree)
            for node in ltree:
                parents = node.get_parents()
                if len(parents) > 1:
                    index_key = node.index
                    required_keys.add(index_key)
                    my_parents = []
                    for parent in parents:
                        if not parent.is_placeholder():
                            if parent in ltree:
                                i = ltree.index(parent)
                                my_parents.append((i, index_key, parent, True))
                    my_parents.sort()
                    a, b, c, d = my_parents[-1]  # @UnusedVariable
                    my_parents[-1] = a, b, c, False
                    sortable_parents += my_parents
            sortable_parents.sort()
            sorted_parents += sortable_parents
        if rotator < 0:
            rotator = len(sorted_parents) - len(required_keys)
        skips = 0
        for i, index_key, parent, can_be_skipped in sorted_parents:
            if index_key in required_keys:
                if skips == rotator or not can_be_skipped:
                    trace_dict[index_key] = parent.save_key
                    required_keys.remove(index_key)
                else:
                    skips += 1
        return rotator, trace_dict



