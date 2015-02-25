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


from kataja.singletons import ctrl
from kataja.Forest import Forest
from kataja.Saved import Savable


class ForestKeeper(Savable):
    """ Container and loader for Forest objects """

    def __init__(self, treelist=None, file_name=None):
        """

        :param List treelist:
        :param StringType file_name:
        """
        Savable.__init__(self, unique=True)
        self.saved.forests = []
        self.saved.current_index = 0
        self.saved.forest = None
        if treelist is None:
            treelist = []
        if treelist:
            self.create_forests(treelist)
        elif file_name:
            self.create_forests_from_file(file_name)

    @property
    def forests(self):
        return self.saved.forests

    @forests.setter
    def forests(self, value):
        self.saved.forests = value

    @property
    def current_index(self):
        return self.saved.current_index

    @current_index.setter
    def current_index(self, value):
        self.saved.current_index = value

    @property
    def forest(self):
        return self.saved.forest

    @forest.setter
    def forest(self, value):
        self.saved.forest = value


    def next_forest(self):
        """

        :return:
        """
        if not self.forests:
            return None
        if self.current_index < len(self.forests) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest

    def prev_forest(self):
        """


        :return:
        """
        if not self.forests:
            return None
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.forests) - 1
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest


    def create_forests_from_file(self, filename):
        """


        :param filename:
        :param StringType filename:
        """
        # f = codecs.open(filename, 'rb', encoding = 'utf-8')
        print(filename)
        try:
            f = open(filename, 'r', encoding='UTF-8')
            treelist = f.readlines()
            f.close()
        except FileNotFoundError:
            treelist = ['[A B]']
        self.create_forests(treelist)

    def create_forests(self, treelist):
        """


        :param treelist:
        :param list treelist:
        """
        self.forests = []
        forest = None
        buildstring_lines = []
        for line in treelist:
            line = line.strip()
            line.split('=', 1)
            parts = line.split('=', 1)
            if line.startswith('#'):
                if forest:
                    forest.add_comment(line[1:])
                else:
                    pass
            elif len(parts) > 1 and not line.startswith('['):  # Definition line
                if not forest:
                    forest = Forest()
                    ctrl.main.set_forest(forest)
                word = parts[0].strip()
                values = parts[1]
                forest.parser.add_definition(word, values)
                # if key== '\gll':
                # forest.setGloss(line)
            elif line.startswith("'"):  # Gloss text
                if forest:
                    if line.endswith("'"):
                        line = line[:-1]
                    forest.gloss_text = line[1:]
            elif forest and not line:  # finalize this forest
                forest.build('\n'.join(buildstring_lines))
                self.forests.append(forest)
                forest = None
            elif line and not forest:  # start a new forest
                buildstring_lines = [line]
                forest = Forest()
                ctrl.main.forest = forest
            elif line and forest:
                buildstring_lines.append(line)
        if forest:  # make sure that the last forest is also added
            forest.build('\n'.join(buildstring_lines))
            self.forests.append(forest)
        self.current_index = 0
        if self.forests:
            if self.forest:
                self.forest.clear_scene()
            self.forest = self.forests[0]
            self.forest.undo_manager.init_if_empty()
            # self.save()



