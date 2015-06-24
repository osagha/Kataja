# coding=utf-8
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

from PyQt5 import QtGui

from kataja.singletons import ctrl
from kataja.Node import Node
from kataja.parser.INodes import IConstituentNode, ITextNode
import kataja.globals as g
from kataja.BaseModel import Synobj

# ctrl = Controller object, gives accessa to other modules



class BaseConstituentNode(Node):
    """ BaseConstituentNodes are minimal graphical representations of constituents. ConstituentNode -class
    inherits this and adds more fields and features, but if you want to create new kind of Constituents in syntax it
    may be cleaner to build on BaseConstituentNode and not ConstituentNode. """
    width = 20
    height = 20
    default_edge_type = g.CONSTITUENT_EDGE
    receives_signals = []
    node_type = g.CONSTITUENT_NODE
    short_name = "BCN"



    # ConstituentNode position points to the _center_ of the node.
    # boundingRect should be (w/-2, h/-2, w, h)

    def __init__(self, constituent=None):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self, syntactic_object=constituent)

        # ------ Bracket drawing -------
        self.left_bracket = None
        self.right_bracket = None
        # ###
        self.selectable = True

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        # ## use update_visibility to change these: visibility of particular elements
        # depends on many factors
        if ctrl.forest:
            self._visibility_brackets = ctrl.forest.settings.bracket_style
        else:
            self._visibility_brackets = 0

        self.setAcceptDrops(True)

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the values.
        2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
        values.
        :return: None
        """
        self.update_features()
        self.update_label()
        self.update_visibility()
        self.announce_creation()
        ctrl.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run the side-effects of various
        setters in an order that makes sense.
        :param updated_fields: list of names of fields that have been updated.
        :return: None
        """
        super().after_model_update(updated_fields, update_type)
        update_label = False
        if 'features' in updated_fields:
            self._inode_changed = True
            self.update_features()
            update_label = True
        if update_label:
            self.update_label()

    # properties implemented by syntactic node
    # set_hooks, to be run when values are set

    def if_changed_features(self, value):
        """ Synobj changed, but remind to update inodes here
        :param value:
        :return:
        """
        self._inode_changed = True
        self.update_features()

    # Other properties

    @property
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            if self.triangle:
                leaves = ITextNode()
                # todo: Use a better linearization here
                for node in ctrl.forest.list_nodes_once(self):
                    if node.is_leaf_node(only_visible=False):
                        leaves += node.label
                        leaves += ' '
                label = leaves.tidy()
            else:
                label = self.label

            self._inode = IConstituentNode(label=label, features=self.features)
            self._inode_changed = False

        return self._inode

    def update_status_tip(self):
        """ Hovering status tip """
        if self.syntactic_object:
            if self.is_leaf_node():
                name = "Leaf constituent"
            elif self.is_root_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            self.status_tip = "%s %s" % (name, self.label)
        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def __str__(self):
        if not self.syntactic_object:
            return 'Placeholder node'
        else:
            return str(self.label)  # + ' adj: %s fixed: %s' % (self.adjustment, self.fixed_position)

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if not self.syntactic_object:
            return '0'
        children = self.get_children()
        if children:
            if len(children) == 2:
                return '[ %s %s ]' % (children[0].as_bracket_string(), children[1].as_bracket_string())
            else:
                return '[ %s ]' % children[0].as_bracket_string()
        else:
            return self.syntactic_object

    def is_placeholder(self):
        """ Constituent structure may assume a constituent to be somewhere, before the user has intentionally created
        one there. These are shown as placeholders, which are nodes, but with limited presence.
        :return: boolean
        """
        return not self.syntactic_object

    def get_attribute_nodes(self, label_key=''):
        """

        :param label_key:
        :return:
        """
        atts = [x.end for x in self.edges_down if x.edge_type == g.ATTRIBUTE_EDGE]
        if label_key:
            for a in atts:
                if a.attribute_label == label_key:
                    return a
        else:
            return atts

    def update_visibility(self, **kw):
        """ Compute visibility-related attributes for this constituent node and update those that depend on this
        -- meaning features etc.

        :param kw:
        """
        was_visible = self.visible
        visible = not self.folded_away
        self.visible = visible

        # Fade in / out
        fade = kw.get('fade', False)
        if fade:
            if visible:
                self.fade_in()
            else:
                self.fade_out()
        else:
            self.setVisible(visible)
        # Label

        label_mode = ctrl.forest.settings.label_style
        if label_mode == g.ALL_LABELS:
            self._label_visible = True
        elif self.triangle:
            self._label_visible = True
        elif self.label and self.is_leaf_node():
            self._label_visible = True
        else:
            self._label_visible = False
        if not self._label_complex:
            self.update_label()
        self._label_complex.setVisible(self._label_visible)

        # ## Edges -- these have to be delayed until all constituents etc nodes know if they are visible
        ctrl.forest.order_edge_visibility_check()

        # ## FeatureNodes
        # ctrl.forest.settings.draw_features
        feat_visible = visible and ctrl.forest.settings.draw_features

        if feat_visible and not was_visible:
            for feature in self.get_features():
                feature.setVisible(True)
        elif was_visible and not feat_visible:
            for feature in self.get_features():
                feature.setVisible(False)

    def reset(self):
        """

        """
        Node.reset(self)
        # self.uses_scope_area = False
        # self.has_visible_brackets = False
        # self.boundingRect(update = True)

    # ### Parents & Children ####################################################

    def is_projecting_to(self, other):
        """

        :param other:
        """
        pass

    def rebuild_brackets(self):
        """ Creates left and right brackets for node, depending on active bracket style.


        """
        def add_left():
            if not self.left_bracket:
                self.left_bracket = ctrl.forest.create_bracket(host=self, left=True)

        def add_right():
            if not self.right_bracket:
                self.right_bracket = ctrl.forest.create_bracket(host=self, left=False)

        def del_left():
            if self.left_bracket:
                f.bracket_manager.delete_bracket(self.left_bracket)
                self.left_bracket = None

        def del_right():
            if self.right_bracket:
                f.bracket_manager.delete_bracket(self.right_bracket)
                self.right_bracket = None

        f = ctrl.forest
        bs = f.settings.bracket_style
        if bs == g.ALL_BRACKETS:
            if self.get_children():
                add_left()
                add_right()
            else:
                del_left()
                del_right()
        elif bs == g.MAJOR_BRACKETS:
            should_have = False
            for edge in self.get_edges_up():
                if edge.alignment == g.LEFT:
                    should_have = True
                    break
            if should_have:
                add_left()
                add_right()
            else:
                del_left()
                del_right()
        elif bs == g.NO_BRACKETS:
            del_left()
            del_right()

    # ### Features #########################################

    # !!!! Shouldn't be done this way. In forest, create a feature, then connect it to ConstituentNode and let Forest's
    # methods to take care that syntactic parts are reflected properly. ConstituentNode shouldn't be modifying its
    # syntactic component.
    # def set_feature(self, syntactic_feature=None, key=None, value=None, string=''):
    #     """ Convenience method for assigning a new feature node related to this constituent.
    #     can take syntactic feature, which is assumed to be already assigned for the syntactic constituent.
    #         Can take key, value pair to create new syntactic feature object, and then a proper feature object is created from this.
    #     :param syntactic_feature:
    #     :param key:
    #     :param value:
    #     :param string:
    #     """
    #     assert self.syntactic_object
    #     if syntactic_feature:
    #         if ctrl.forest.settings.draw_features:
    #             ctrl.forest.create_feature_node(self, syntactic_feature)
    #     elif key:
    #         sf = self.syntactic_object.set_feature(key, value)
    #         self.set_feature(syntactic_feature=sf)
    #     elif string:
    #         features = ctrl.forest.parse_features(string, self)
    #         if 'gloss' in features:
    #             self.gloss = features['gloss']
    #             del features['gloss']
    #         for feature in features.values():
    #             self.set_feature(syntactic_feature=feature)
    #         self.update_features()


    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children_of_type(edge_type=g.FEATURE_EDGE)

    def update_features(self):
        """


        """
        pass
        # if not self.syntactic_object:
        # return
        # current_features = set([x.syntactic_object.get() for x in self.get_features()])
        # correct_features = self.syntactic_object.features
        # print(current_features, correct_features)
        # for key, item in correct_features.items():
        # if key not in current_features:
        # self.set_feature(syntactic_feature=item, key=key)
        # else:
        # current_features.remove(key)
        # if current_features:
        # print('leftover features:', current_features)

    # ### Labels #############################################

    # things to do with traces:
    # if renamed and index is removed/changed, update chains
    # if moved, update chains
    # if copied, make sure that copy isn't in chain
    # if deleted, update chains
    # any other operations?

    def is_empty_node(self):
        """ Empty nodes can be used as placeholders and deleted or replaced without structural worries """
        return (not self.label) and self.is_leaf_node()

    def get_features_as_string(self):
        """


        :return:
        """
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [str(f) for f in features]
        return ', '.join(feature_strings)

    # ## Multidomination #############################################

    def is_multidominated(self):
        """ Check if the ConstituentNode has more than one parent. """
        return len(self.get_parents()) > 1

    def get_c_commanded(self):
        """ Returns the closest c-commanded elements of this element. All dominated by those are also c-commanded """
        result = []
        for parent in self.get_parents():
            for child in parent.get_children():
                if child is not self:
                    result.append(child)
        return result

    # ## Qt overrides ######################################################################

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        painter.setPen(self.contextual_color)
        if ctrl.pressed == self:
            rect = True
        elif self._hovering:
            rect = True
        elif ctrl.is_selected(self):
            rect = True
        elif self.left_bracket:
            rect = False
        else:
            rect = False
        if self.triangle:
            self.paint_triangle(painter)
        elif rect:
            painter.drawRect(self.inner_rect)
            # if self.uses_scope_area:
            # self.paint_scope_rect(painter, rect)
        # Node.paint(self, painter, option, widget)


    def open_embed(self):
        """ """
        ctrl.ui.start_constituent_editing(self)

    # ### Selection ########################################################

    def refresh_selection_status(self, selected):
        """

        :param selected:
        """
        self.effect.setEnabled(selected)
        self.update()

    # ### Checks for callable actions ####

    def can_root_merge(self):
        """
        :return:
        """
        root = self.get_root_node()
        return self is not root and self is not root.left(only_visible=False)

    # ### Dragging #####################################################################

    # ## Most of this is implemented in Node

    def prepare_children_for_dragging(self):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        nodes_in_tree = ctrl.forest.list_nodes_once(self.get_root_node())
        parent_index = nodes_in_tree.index(self)
        for node in ctrl.forest.list_nodes_once(self):
            if node is not ctrl.dragged_focus and nodes_in_tree.index(node) > parent_index:
                node.add_to_dragged()


    #################################

    @property
    def hovering(self):
        """


        :return:
        """
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects
        Overrides Node.set_hovering.
        :param value: bool
        :return:
        """
        if self.left_bracket:
            self.left_bracket.hovering = value
        if self.right_bracket:
            self.right_bracket.hovering = value
        self._set_hovering(value)

    # ### Suggestions for completing missing aspects (active for selected nodes)
    def add_completion_suggestions(self):
        """ Node has selected and if it is a placeholder or otherwise lacking, it may suggest an
         option to add a proper node here.
        """
        if self.is_placeholder():
            ctrl.ui.create_touch_area(self, g.TOUCH_ADD_CONSTITUENT)

    def dropEvent(self, event):
        """

        :param event:
        """
        print("CN dropEvent")

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Attributes from synobj and their setter hooks
    features = Synobj("features", if_changed=if_changed_features)