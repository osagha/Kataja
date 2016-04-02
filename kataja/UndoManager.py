# -*- coding: UTF-8 -*-
""" UndoManager is an object in a forest to store the previous states of the forest and to restore these states.
"""
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
import pprint

from kataja.utils import time_me
from kataja.singletons import ctrl

# Creation/Deletion flags
CREATED = 1
DELETED = 2

class UndoManager:
    """ Holds the undo stack and manages the undo- and redo-activities. """

    def __init__(self, forest):
        self.forest = forest
        self.full_state = {}
        self._stack = []
        self._current = 0

    @time_me
    def take_snapshot(self, msg=''):
        """ Store changes from ctrl.undo_pile and put them here into undo_stack.
        :param msg: str = msg to
        :return: None
        """
        # save objects in undo pile
        snapshot = {}
        for obj in ctrl.undo_pile:
            transitions, transition_type = obj.transitions()
            snapshot[obj.save_key] = (obj, transitions, transition_type)
            obj.flush_history()
        # ...
        if snapshot:
            self._stack = self._stack[:self._current + 1]
            self._stack.append((msg, snapshot))
            self._current = len(self._stack) - 1
        ctrl.undo_pile = set()
        ctrl.add_message('took snapshot, undo stack size: %s items %s chars' % (
            len(self._stack), len(str(self._stack))))
        print('stack len:', len(str(self._stack)))

    def undo(self):
        """ Move backward in the undo stack
        :return: None
        """
        if not self._stack:
            return
        if self._current == 0:
            ctrl.add_message('undo [%s]: Cannot undo further' % self._current)
            return
        ctrl.disable_undo()
        ctrl.multiselection_start()
        ctrl.forest.halt_drawing = True
        msg, snapshot = self._stack[self._current]
        affected = set()
        for obj, transitions, transition_type in snapshot.values():
            obj.revert_to_earlier(transitions)
            if transition_type == CREATED:
                ctrl.forest.delete_item(obj, ignore_consequences=True)
            elif transition_type == DELETED:
                ctrl.forest.add_to_scene(obj)
            affected.add(obj)
            if hasattr(obj, 'update_visibility'):
                obj.update_visibility()
        ctrl.forest.edge_visibility_check()
        for obj, transitions, transition_type in snapshot.values():
            if transition_type == CREATED:
                revtt = DELETED
            elif transition_type == DELETED:
                revtt = CREATED
            else:
                revtt = transition_type
            obj.after_model_update(transitions.keys(), revtt)
            if getattr(obj.__class__, 'syntactic_object', False):
                node = ctrl.forest.nodes_from_synobs.get(obj.save_key, None)
                if node and node not in affected:
                    node.after_model_update([], revtt)
        ctrl.forest.flush_and_rebuild_temporary_items()
        ctrl.add_message('undo [%s]: %s' % (self._current, msg))
        ctrl.multiselection_end()
        ctrl.resume_undo()
        self._current -= 1
        ctrl.forest.halt_drawing = False

        print('-------undo finished', self._current)

    def redo(self):
        """ Move forward in the undo stack
        :return: None
        """
        if self._current < len(self._stack) - 1:
            self._current += 1
        else:
            ctrl.add_message('redo [%s]: In last action' % self._current)
            return
        ctrl.disable_undo()
        ctrl.multiselection_start()
        ctrl.forest.halt_drawing = True
        msg, snapshot = self._stack[self._current]
        affected = set()
        for obj, transitions, transition_type in snapshot.values():
            obj.move_to_later(transitions)
            if transition_type == CREATED:
                ctrl.forest.add_to_scene(obj)
            elif transition_type == DELETED:
                ctrl.forest.delete_item(obj, ignore_consequences=True)
            affected.add(obj)
        ctrl.forest.edge_visibility_check()
        for obj, transitions, transition_type in snapshot.values():
            obj.after_model_update(transitions.keys(), transition_type)
            if getattr(obj.__class__, 'syntactic_object', False):
                node = ctrl.forest.nodes_from_synobs.get(obj.save_key, None)
                if node and node not in affected:
                    node.after_model_update([], transition_type)
        ctrl.forest.flush_and_rebuild_temporary_items()
        ctrl.add_message('redo [%s]: %s' % (self._current, msg))
        ctrl.multiselection_end()
        ctrl.resume_undo()
        ctrl.forest.halt_drawing = False
        print('------redo finished: ', msg, self._current)

    @staticmethod
    def dump_dict_to_file(undo_dict, filename='undo_dump'):
        """ Debug method, does what it says.
        :param undo_dict: can be any dict
        :param filename: default is 'undo_dump'
        """
        f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=4, stream=f)
        pp.pprint(undo_dict)
        f.close()
