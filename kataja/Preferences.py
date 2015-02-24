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

import os
from pathlib import Path
import plistlib
from collections import OrderedDict
import sys

from PyQt5 import QtGui, QtCore

from kataja.globals import *
from kataja.utils import time_me


disable_saving_preferences = True
# Alternatives: Cambria Math, Asana Math, XITS Math

mac_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Monaco', 'Normal', 10],
             UI_FONT: ['Helvetica', 'Normal', 10], BOLD_FONT: ['STIX', 'Bold', 12],
             ITALIC_FONT: ['Asana Math', 'Italic', 12], SMALL_CAPS: ['Lao MN', 'Normal', 10],
             SMALL_FEATURE: ['Lao MN', 'Normal', 7]}

linux_fonts = {MAIN_FONT: ['Asana Math', 'Normal', 12], CONSOLE_FONT: ['Courier', 'Normal', 10],
               UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Asana Math', 'Italic', 12],
               BOLD_FONT: ['STIX', 'Bold', 12], SMALL_CAPS: ['Lao MN', 'Normal', 9],
               SMALL_FEATURE: ['Lao MN', 'Normal', 7]}

wfont = 'Cambria'
windows_fonts = {MAIN_FONT: ['Cambria', 'Normal', 10], CONSOLE_FONT: ['Consolas', 'Normal', 10],
                 UI_FONT: ['Droid Sans', 'Normal', 10], ITALIC_FONT: ['Cambria', 'Italic', 10],
                 BOLD_FONT: ['Cambria', 'Bold', 10], SMALL_CAPS: ['Lao MN', 'Normal', 8],
                 SMALL_FEATURE: ['Lao MN', 'Normal', 7]}

print('platform:', sys.platform)
if sys.platform == 'darwin':
    fonts = mac_fonts
elif sys.platform == 'win32':
    fonts = windows_fonts
else:
    fonts = linux_fonts

color_modes = OrderedDict([('solarized_dk', {'name': 'Solarized dark', 'fixed': True, 'hsv': [0, 0, 0]}),
                           ('solarized_lt', {'name': 'Solarized light', 'fixed': True, 'hsv': [0, 0, 0]}),
                           ('random', {'name': 'Random for each treeset', 'fixed': False, 'hsv': [0, 0, 0]}),
                           ('print', {'name': 'Print-friendly', 'fixed': True, 'hsv': [0.2, 0.2, 0.2]}),
                           ('bw', {'name': 'Black and white', 'fixed': True, 'hsv': [0, 0, 0]}),
                           ('random-light', {'name': 'Random on a light background', 'fixed': False, 'hsv': [0, 0, 0]}),
                           ('random-dark', {'name': 'Against a dark background', 'fixed': False, 'hsv': [0, 0, 0]})])


class Preferences(object):
    """ Settings that affect globally, these can be pickled, but QtPreferences not. Primary singleton object, needs to support saving and loading. 

    Preferences should follow the following progression:

    element properties < forest settings < preferences

    Preferences is the largest group. It includes global preferences and default values for forest settings. If forest settings doesn't have a value set, it is get from preferences. Similarly if element doesn't have a property set, it is get from forest settings, and ultimately from preferences.

    This means that the implementation for getting and setting is done mostly in elements and in forest settings. Preferences it self can be written and read directly.

    """
    # Prefs are not saved in save command, but changes here are undoable, so this must support the save protocol.
    not_saved = ['resources_path', 'default_userspace_path', 'in_app']


    def __init__(self):
        self.save_key = 'preferences'
        self.draw_width = .5
        self.selection_width = 0.8
        self.thickness_multiplier = 2
        self.color_modes = color_modes
        self.shared_palettes = {}

        self.dpi = 300
        self.FPS = 30
        self.fps_in_msec = 1000 / self.FPS
        self.default_visualization = 'Left first tree'

        self.blender_app_path = '/Applications/blender.app/Contents/MacOS/blender'
        self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        self.move_frames = 12
        self._curve = 'InQuad'

        # ## Default structural rules that apply to new trees
        self.default_use_projection = True
        self.default_who_projects = 'left_external'
        self.default_use_multidomination = True
        self.default_binary_branching = False

        # ## Default settings for new trees
        self.default_label_style = 2
        self.default_uses_multidomination = True
        self.default_traces_are_grouped_together = 0
        self.default_shows_constituent_edges = True
        self.default_shows_merge_order = False
        self.default_shows_select_order = False
        self.default_draw_features = True
        self.default_draw_width = 2
        self.my_palettes = {}
        self.default_color_mode = 'solarized_dk'
        self.default_hsv = None
        self.default_bracket_style = 0

        # ## Global preferences
        self.color_mode = self.default_color_mode
        self.fonts = fonts
        self.keep_vertical_order = False
        self.use_magnets = True
        self.edge_width = 20  # 20
        self.edge_height = 20
        self.hanging_gloss = True
        self.spacing_between_trees = 3
        self.include_features_to_label = False
        self.constituency_edge_shape = 1
        self.feature_edge_shape = 3
        self.console_visible = False
        self.ui_speed = 8
        self.touch = True

        my_path = Path(__file__).parts
        if sys.platform == 'darwin' and 'Kataja.app' in my_path:
            print(my_path)
            i = my_path.index('Kataja.app')
            self.resources_path = str(Path(*list(my_path[:i + 1]) + ['Contents', 'Resources', 'resources', ''])) + '/'
            self.default_userspace_path = '~/'
            self.in_app = True
        else:
            self.resources_path = './resources/'
            self.default_userspace_path = './'
            self.in_app = False
        print("resources_path: ", self.resources_path)
        print("default_userspace_path: ", self.default_userspace_path)
        self.userspace_path = ''
        self.debug_treeset = self.resources_path + 'trees.txt'
        self.file_name = 'savetest.kataja'
        self.print_file_path = ''
        self.print_file_name = 'kataja_print'
        self.include_gloss_to_print = True

        # ## Default edge settings
        # Edge types
        # CONSTITUENT_EDGE = 1
        # FEATURE_EDGE = 2
        # GLOSS_EDGE = 3
        # ARROW = 4
        # PROPERTY_EDGE = 5
        # ABSTRACT_EDGE = 0
        # ATTRIBUTE_EDGE = 6

        self.edges = {
            CONSTITUENT_EDGE: {'shape_name': 'shaped_cubic', 'color': 'content1', 'pull': .24, 'visible': True,
                               'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            FEATURE_EDGE: {'shape_name': 'cubic', 'color': 'accent2', 'pull': .32, 'visible': True,
                           'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            GLOSS_EDGE: {'shape_name': 'cubic', 'color': 'accent4', 'pull': .40, 'visible': True,
                         'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ARROW: {'shape_name': 'linear', 'color': 'accent4', 'pull': 0, 'visible': True, 'arrowhead_at_start': False,
                    'arrowhead_at_end': True, 'font': SMALL_CAPS, 'labeled': True},
            DIVIDER: {'shape_name': 'linear', 'color': 'accent6', 'pull': 0, 'visible': True,
                      'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': SMALL_CAPS, 'labeled': True,
                      'style': 'dashed'},
            PROPERTY_EDGE: {'shape_name': 'linear', 'color': 'accent5', 'pull': .40, 'visible': True,
                            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ABSTRACT_EDGE: {'shape_name': 'linear', 'color': 'content1', 'pull': .40, 'visible': True,
                            'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False},
            ATTRIBUTE_EDGE: {'shape_name': 'linear', 'color': 'content1', 'pull': .50, 'visible': True,
                             'arrowhead_at_start': False, 'arrowhead_at_end': False, 'labeled': False}, }

        ### Default node settings
        # Node types
        # ABSTRACT_NODE = 0
        # CONSTITUENT_NODE = 1
        # FEATURE_NODE = 2
        # ATTRIBUTE_NODE = 3
        # GLOSS_NODE = 4
        # PROPERTY_NODE = 5
        self.nodes = {ABSTRACT_NODE: {'color': 'content1', 'font': MAIN_FONT, 'font-size': 10},
                      CONSTITUENT_NODE: {'color': 'content1', 'font': MAIN_FONT, 'font-size': 10},
                      FEATURE_NODE: {'color': 'accent2', 'font': SMALL_CAPS, 'font-size': 9},
                      ATTRIBUTE_NODE: {'color': 'accent4', 'font': SMALL_CAPS, 'font-size': 10},
                      GLOSS_NODE: {'color': 'accent5', 'font': ITALIC_FONT, 'font-size': 10},
                      PROPERTY_NODE: {'color': 'accent6', 'font': SMALL_CAPS, 'font-size': 10},
                      COMMENT_NODE: {'color': 'accent4', 'font': MAIN_FONT, 'font-size': 14}}
        self.custom_colors = {}


    def update(self, update_dict):
        """

        :param update_dict:
        """
        for key, value in update_dict.items():
            setattr(self, key, value)


    def add_color_mode(self, color_key, hsv, color_settings):
        """

        :param color_key:
        :param hsv:
        :param color_settings:
        """
        self.color_modes[color_key] = {'name': color_settings.get_color_name(hsv), 'fixed': True, 'hsv': hsv}


    # ##### Save & Load ########################################


    def save_preferences(self):
        """ Save preferences uses QSettings, which is Qt:s abstraction over platform-dependant ini/preferences files.
        It doesn't need any parameters,
        """

        if disable_saving_preferences:
            return

        settings = QtCore.QSettings()
        settings.clear()
        d = vars(self)
        for key, value in d.items():
            if key in Preferences.not_saved:
                continue
            if isinstance(value, dict):
                settings.beginGroup(key)
                for dkey, dvalue in value.items():
                    settings.setValue(str(dkey), dvalue)
                settings.endGroup()
            else:
                settings.setValue(key, value)


    def load_preferences(self):

        if disable_saving_preferences:
            return

        settings = QtCore.QSettings()
        for key, default_value in vars(self).items():
            if key in Preferences.not_saved:
                continue
            if isinstance(default_value, dict):
                settings.beginGroup(key)
                d = getattr(self, key)
                for dkey in settings.childKeys():
                    d[dkey] = settings.value(dkey, None)
                setattr(self, key, d)
            else:
                setattr(self, key, settings.value(key, default_value))


def extract_bitmaps(filename):
    """
    Helper method to turn 3-color image (blue, black, transparent) into bitmap masks.
    :param filename:
    :return: tuple(original as pixmap, color1 as mask (bitmap), color2 as mask)
    """
    pm = QtGui.QPixmap(filename)
    color1 = QtGui.QColor(0, 0, 255)
    color2 = QtGui.QColor(0, 0, 0)
    bms = (
        pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskOutColor),
        pm.createMaskFromColor(color2, QtCore.Qt.MaskOutColor))
    return bms


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        pass

    def late_init(self, preferences, fontdb):  # called when Qt app exists
        # graphics and fonts can be initiated only when QApplication exists
        """

        :param preferences:
        :param fontdb:
        """
        iconpath = preferences.resources_path + 'icons/'

        def pixmap(path, width=0):
            p = QtGui.QPixmap(iconpath + path)
            if width:
                p.scaledToWidth(width)
            return p

        print("font families:", QtGui.QFontDatabase().families())
        self.easing_curve = []
        self.prepare_fonts(preferences.fonts, fontdb, preferences)
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.NoBrush)
        self.lock_icon = pixmap('lock.png', 16)
        self.cut_icon = pixmap('cut_icon48.png', 24)
        self.delete_icon = pixmap('backspace48.png', 24)
        self.close_icon = pixmap('close24.png')
        self.fold_icon = pixmap('less24.png')
        self.more_icon = pixmap('more24.png')
        self.pin_drop_icon = pixmap('pin_drop24.png')
        self.left_arrow = extract_bitmaps(iconpath + 'left_2c.gif')
        self.right_arrow = extract_bitmaps(iconpath + 'right_2c.gif')
        self.add_icon = pixmap('add24.png')
        self.add_box_icon = pixmap('add_box24.png')
        self.settings_icon = pixmap('settings24.png')
        self.triangle_icon = pixmap('triangle48.png')
        self.triangle_close_icon = pixmap('triangle_close48.png')
        self.kataja_icon = pixmap('kataja.png')
        # self.gear_icon = extract_bitmaps(preferences.resources_path+'icons/gear2_16.gif')

    def update(self, preferences):
        """

        :param preferences:
        """
        self.prepare_fonts(preferences.fonts)
        self.prepare_easing_curve(preferences._curve, preferences.move_frames)


    def prepare_easing_curve(self, curve_type, frames):
        """

        :param curve_type:
        :param frames:
        :return:
        """
        curve = QtCore.QEasingCurve(getattr(QtCore.QEasingCurve, curve_type))

        def curve_value(x):
            """

            :param x:
            :return:
            """
            z = 1.0 / frames
            y = float(x) / frames
            return z + y - curve.valueForProgress(y)

        self.easing_curve = [curve_value(x) for x in range(frames)]
        # self.easing_curve = [(1.0 / self.move_frames) + (float(x) / self.move_frames) - curve.valueForProgress(float(x) / self.move_frames) for x in range(self.move_frames)]
        # self.easing_curve=[(float(x)/self.move_frames)-curve.valueForProgress(float(x)/self.move_frames) for x in range(self.move_frames)]
        s = sum(self.easing_curve)
        self.easing_curve = [x / s for x in self.easing_curve]

    def prepare_fonts(self, fonts_dict, fontdb, preferences):
        """

        :param fonts_dict:
        :param fontdb:
        """
        print('preparing fonts...')
        self.fonts = {}
        for key, font_tuple in fonts_dict.items():
            name, style, size = font_tuple
            font = fontdb.font(name, style, size)
            print(name, font.exactMatch())
            if name == 'Asana Math':  # and not font.exactMatch():
                print('Loading Asana Math locally')
                fontdb.addApplicationFont(preferences.resources_path + "Asana-Math.otf")
                font = fontdb.font(name, style, size)
            if style == 'Italic':
                font.setItalic(True)
            self.fonts[key] = font
        font = QtGui.QFontMetrics(self.fonts[MAIN_FONT])  # it takes 2 seconds to get FontMetrics
        print('font leading: %s font height: %s ' % (font.leading(), font.height()))
        main = self.fonts[MAIN_FONT]
        main.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.font_space_width = font.width(' ')
        self.font_bracket_width = font.width(']')
        self.font_bracket_height = font.height()
        print('font metrics: ', font)
        # print(self.font_space_width, self.font_bracket_width, self.font_bracket_height)
        self.fonts[SMALL_CAPS].setCapitalization(QtGui.QFont.SmallCaps)

    ### Font helper ###

    def font(self, name):
        return self.fonts[name]

        # return self.fonts.get(name, self.fonts[MAIN_FONT])

    def get_key_for_font(self, font):
        """ Find the key for given QFont. Keys are cheaper to store than actual fonts.
        If matching font is not found in current font dict, it is created as custom_n
        :param font: QFont
        :return: string
        """
        for key, value in self.fonts.items():
            if font == value:
                return key
        key_suggestion = 'custom_1'
        i = 1
        while key_suggestion in self.fonts:
            i += 1
            key_suggestion = 'custom_%s' % i
        self.fonts[key_suggestion] = font
        return key_suggestion

