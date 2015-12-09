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

from PyQt5 import QtGui, QtCore

from kataja.globals import *

disable_saving_preferences = False
# Alternatives: Cambria Math, Asana Math, XITS Math

curves = ['Linear', 'InQuad', 'OutQuad', 'InOutQuad', 'OutInQuad', 'InCubic', 'OutCubic',
          'InOutCubic', 'OutInCubic', 'InQuart', 'OutQuart', 'InOutQuart', 'OutInQuart', 'InQuint',
          'OutQuint', 'InOutQuint', 'OutInQuint', 'InSine', 'OutSine', 'InOutSine', 'OutInSine',
          'InExpo', 'OutExpo', 'InOutExpo', 'OutInExpo', 'InCirc', 'OutCirc', 'InOutCirc',
          'OutInCirc', 'InElastic', 'OutElastic', 'InOutElastic', 'OutInElastic', 'InBack',
          'OutBack', 'InOutBack', 'OutInBack', 'InBounce', 'OutBounce', 'InOutBounce',
          'OutInBounce']

def extract_bitmaps(filename):
    """
    Helper method to turn 3-color image (blue, black, transparent) into
    bitmap masks.
    :param filename:
    :return: tuple(original as pixmap, color1 as mask (bitmap), color2 as mask)
    """
    pm = QtGui.QPixmap(filename)
    color1 = QtGui.QColor(0, 0, 255)
    color2 = QtGui.QColor(0, 0, 0)
    bms = (pm, pm.createMaskFromColor(color1, QtCore.Qt.MaskOutColor),
           pm.createMaskFromColor(color2, QtCore.Qt.MaskOutColor))
    return bms


class Preferences(object):
    """ Settings that affect globally, these can be pickled,
    but QtPreferences not. Primary singleton object, needs to
    support saving and loading.

    Preferences should follow the following progression:

    element properties < forest settings < preferences

    Preferences is the largest group. It includes global preferences and
    default values for forest settings.
    If forest settings doesn't have a value set, it is get from preferences.
    Similarly if element doesn't have a
    property set, it is get from forest settings, and ultimately from
    preferences.

    This means that the implementation for getting and setting is done mostly
    in elements and in forest settings.
    Preferences it self can be written and read directly.

    preferences with underscore are not saved, they can be used for information about UI drawing

    """
    # Prefs are not saved in save command, but changes here are undoable,
    # so this must support the save protocol.
    not_saved = ['plugins']

    def __init__(self, running_environment, immutable=False):
        self.save_key = 'preferences'
        self._tab_order = ['General', 'Drawing', 'Printing', 'Syntax', 'Node styles',
                           'Performance', 'Plugins', 'Advanced']

        self.color_mode = 'solarized_lt'
        self._color_mode_ui = {'tab': 'General', 'special': 'color_modes',
                               'label': 'Default colors',
                               'help': 'Color theme used for both trees and editor',
                               'on_change': 'update_colors', 'order': 10}
        self.hsv = None

        self.touch = True
        self._touch_ui = {'tab': 'General', 'order': 20, 'label': 'Touch-friendly UI',
                          'help': 'Draggable items are larger'}

        self.gloss_nodes = True
        self._gloss_nodes_ui = {'tab': 'General', 'order': 30}

        self.feature_nodes = True
        self._feature_nodes_ui = {'tab': 'General', 'order': 31,
                                  'help': 'Draw glosses or features as separate nodes, or include '
                                          'them as lines in constituent nodes.'}

        self.fonts = running_environment.fonts
        self._fonts_ui = {'tab': 'General', 'special': 'fonts'}

        self.large_ui_text = False
        self._large_ui_text_ui = {'tab': 'General',
                                  'label': 'Big UI',
                                  'help': 'Force user interface to use at least 14pt font.',
                                  'on_change': 'resize_ui_font', 'order': 40}

        self.visualization = 'Left first trees'
        self._visualization_ui = {'tab': 'Drawing', 'special': 'visualizations',
                                  'help': 'Default visualization for new trees.',
                                  'order': 10,
                                  'on_change': 'update_visualization'}

        self.thickness_multiplier = 2
        self._thickness_multiplier = {'tab': 'Drawing', 'range': (0.5, 6), 'order': 50, 'help':
                                      'If the visualization draws some edges as thicker, '
                                      'this defines how much thicker.'}

        self.bracket_style = 0
        self._bracket_style_ui = {'tab': 'Drawing', 'choices':
                                  [(0, 'No brackets'),
                                   (1, 'Non-obvious brackets'),
                                   (2, 'All brackets')],
                                  'label': 'Draw brackets',
                                  'help': 'When to draw brackets. Visualizations may override '
                                          'this.',
                                  'order': 30}

        self.use_magnets = 2
        self._use_magnets_ui = {'tab': 'Drawing', 'choices':
                                [(0, 'Aim at center of node'),
                                 (1, 'Magnets at top and bottom'),
                                 (2, 'Align magnets to parent')],
                                'help': 'Branches can link to "magnets" in node outlines, '
                                        'and magnet placement may be affected by parent node',
                                'order': 40}

        self.edge_width = 20  # 20
        self._edge_width_ui = {'tab': 'Drawing', 'range': (0, 60), 'order': 20}

        self.edge_height = 20
        self._edge_height_ui = {'tab': 'Drawing', 'range': (0, 60), 'order': 21,
                                'help': 'Default width and height for branches'}

        self.spacing_between_trees = 3
        self._spacing_between_trees_ui = {'tab': 'Drawing', 'range': (0, 4),
                                          'help': 'When there are several trees algorithms try to '
                                                  'use multiples of "edge width" as padding '
                                                  'between trees.'}

        self.user_palettes = {}
        self.traces_are_grouped_together = False
        self.shows_constituent_edges = True

        self.dpi = 300
        self._dpi_ui = {'tab': 'Printing', 'choices': [72, 150, 300, 450, 600], 'label': 'DPI',
                        'help': 'Dots Per Inch setting when exporting images', 'order': 20}

        self.print_format = 'pdf'
        self._print_format_ui = {'tab': 'Printing', 'choices': ['pdf', 'png'], 'order': 10}

        self.print_file_path = ''
        self._print_file_path_ui = {'tab': 'Printing', 'type': 'folder', 'order': 30,
                                    'label': 'Quick print path'}

        self.print_file_name = 'kataja_print'
        self._print_file_name_ui = {'tab': 'Printing', 'type': 'text', 'order': 31,
                                    'label': 'Quick print file name',
                                    'help': 'Quick print (Ctrl-p) will print a snapshot of the '
                                            'current tree into a file, file names will be '
                                            'generated as "katajaprint.pdf", "katajaprint1.pdf", '
                                            '"katajaprint2.pdf"... and so on.'}

        self.include_gloss_to_print = True
        self._include_gloss_to_print_ui = {'tab': 'Printing'}

        self.use_projection = True
        self._use_projection_ui = {'tab': 'Syntax'}

        self.who_projects = 'left_external'
        self._who_projects_ui = {'tab': 'Syntax'}

        self.uses_multidomination = True
        self._uses_multidomination_ui = {'tab': 'Syntax'}

        self.binary_branching = False
        self._binary_branching_ui = {'tab': 'Syntax'}

        self.shows_merge_order = False
        self._shows_merge_order_ui = {'tab': 'Syntax'}

        self.shows_select_order = False
        self._shows_select_order_ui = {'tab': 'Syntax'}

        # Rest of the edges are defined in their corresponding node classes
        self.edges = {
            ARROW: {'shape_name': 'linear', 'color': 'accent4', 'pull': 0, 'visible': True,
                    'arrowhead_at_start': False, 'arrowhead_at_end': True, 'font': SMALL_CAPS,
                    'labeled': True},
            DIVIDER: {'shape_name': 'linear', 'color': 'accent6', 'pull': 0, 'visible': True,
                      'arrowhead_at_start': False, 'arrowhead_at_end': False, 'font': SMALL_CAPS,
                      'labeled': True, 'style': 'dashed'}}
        # Nodes are defined in their classes and preference dict is generated
        #  from those.
        self.nodes = {}
        self._nodes_ui = {'tab': 'Node styles', 'special': 'nodes'}
        self.node_types_order = []

        self.plugins = {}
        self._plugins_ui = {'tab': 'Plugins', 'special': 'plugins'}

        self.FPS = 60
        self._FPS_ui = {'tab': 'Performance', 'range': (10, 60), 'label': 'Target FPS'}
        self._fps_in_msec = 1000 / self.FPS

        self.move_frames = 12
        self._move_frames_ui = {'tab': 'Performance', 'range': (0, 30),
                                'on_change': 'prepare_easing_curve', 'label': 'Animation frames'}
        self.curve = 'InQuad'
        self._curve_ui = {'tab': 'Performance', 'choices': curves,
                                 'on_change': 'prepare_easing_curve',
                          'help': 'Easing curve used to compute the intermediate steps in '
                                  'animations. Some options are just silly.'}
        self.my_palettes = {}

        self.move_effect = False
        self._move_effect_ui = {'tab': 'Performance',
                                'help': "Adds movement blur. Experimental and quite broken, "
                                        "especially in high DPI displays."}
        self.glow_effect = False
        self._glow_effect_ui = {'tab': 'Performance',
                                "help": "Glow effect for selected nodes. "
                                        "Doesn't work well on high DPI screens."}


        # self.blender_app_path =
        # '/Applications/blender.app/Contents/MacOS/blender'
        # self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        self.userspace_path = running_environment.default_userspace_path
        self.debug_treeset = running_environment.resources_path + 'trees.txt'
        self.file_name = 'savetest.kataja'

        self.custom_colors = {}

    def import_node_classes(self, node_classes):
        for key, nodeclass in node_classes.items():
            nd = nodeclass.default_style.copy()
            nd['name'] = nodeclass.name[0]
            nd['name_pl'] = nodeclass.name[1]
            nd['display'] = nodeclass.display
            nd['short_name'] = nodeclass.short_name
            self.nodes[key] = nd
            edge_key = nodeclass.default_style['edge']
            if nd['display']:
                self.node_types_order.append(key)
            self.edges[edge_key] = nodeclass.default_edge.copy()
        self.node_types_order.sort()

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
        # Undo support for this?
        self.user_palettes[color_key] = {'name': color_settings.get_color_name(hsv), 'fixed': True,
                                         'hsv': hsv}
        color_settings.update_color_modes()

    def copy_preferences_from(self, source):
        for key, default_value in vars(self).items():
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            setattr(self, key, getattr(source, key))

    # ##### Save & Load ########################################

    def save_preferences(self):
        """ Save preferences uses QSettings, which is Qt:s abstraction over
        platform-dependant ini/preferences files.
        It doesn't need any parameters,
        """
        def recursive_write(settings, k, v):
            k = str(k)
            if isinstance(v, dict):
                settings.beginGroup(k)
                for kk, vv in v.items():
                    recursive_write(settings, str(kk), vv)
                settings.endGroup()
            else:
                settings.setValue(k, v)

        if disable_saving_preferences:
            return

        settings = QtCore.QSettings()
        settings.clear()
        d = vars(self)
        for key, value in d.items():
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            recursive_write(settings, key, value)
        settings.sync()

    def load_preferences(self):

        def recursive_load(settings, k, dv, d=None):
            if isinstance(dv, dict):
                settings.beginGroup(k)
                nd = getattr(self, k)
                for kk in settings.childKeys():
                    recursive_load(settings, kk, None, nd)
                if d:
                    d[k] = nd
                else:
                    setattr(self, k, nd)
                settings.endGroup()
                return
            value = settings.value(k, dv)
            if isinstance(dv, float):
                value = float(value)
            elif isinstance(dv, bool):
                value = bool(value)
            elif isinstance(dv, int):
                value = int(value)
            if d:
                d[k] = value
            else:
                setattr(self, k, value)

        if disable_saving_preferences:
            return

        settings = QtCore.QSettings()
        for key, default_value in vars(self).items():
            if key.startswith('_') or key in Preferences.not_saved:
                continue
            recursive_load(settings, key, default_value)


class QtPreferences:
    """ Preferences object that holds derived Qt objects like fonts and
    brushes. """

    def __init__(self):  # called to create a placeholder in early imports
        self.easing_curve = []
        self.fontdb = None
        self.no_pen = None
        self.no_brush = None
        self.lock_icon = None
        self.lock_pixmap = None
        self.cut_icon = None
        self.delete_icon = None
        self.close_icon = None
        self.fold_icon = None
        self.more_icon = None
        self.pin_drop_icon = None
        self.left_arrow = None
        self.right_arrow = None
        self.add_icon = None
        self.add_box_icon = None
        self.settings_icon = None
        self.settings_pixmap = None
        self.triangle_icon = None
        self.triangle_close_icon = None
        self.font_icon = None
        self.kataja_icon = None

    def late_init(self, running_environment, preferences, fontdb):  # called when Qt app exists
        # graphics and fonts can be initiated only when QApplication exists
        """

        :param preferences:
        :param fontdb:
        """
        iconpath = running_environment.resources_path + 'icons/'

        def pixmap(path, width=0):
            """

            :param path:
            :param width:
            :return:
            """
            p = QtGui.QPixmap(iconpath + path)
            p.setDevicePixelRatio(2.0)
            if width:
                p = p.scaledToWidth(width)
            return p

        def icon(path):
            """

            :param path:
            :param width:
            :return:
            """
            p = QtGui.QIcon(iconpath + path)
            return p

        # print("font families:", QtGui.QFontDatabase().families())
        self.fontdb = fontdb
        self.prepare_fonts(preferences.fonts, running_environment)
        self.prepare_easing_curve(preferences.curve, preferences.move_frames)
        self.toggle_large_ui_font(preferences.large_ui_text, preferences.fonts)
        self.no_pen = QtGui.QPen()
        self.no_pen.setStyle(QtCore.Qt.NoPen)
        self.no_brush = QtGui.QBrush()
        self.no_brush.setStyle(QtCore.Qt.NoBrush)
        self.lock_icon = icon('lock32.png')
        self.lock_pixmap = pixmap('lock32.png', 16)
        self.cut_icon = icon('cut_icon48.png')
        self.delete_icon = icon('backspace48.png')
        self.close_icon = icon('close24.png')
        self.fold_icon = icon('less24.png')
        self.more_icon = icon('more24.png')
        self.pin_drop_icon = icon('pin_drop24.png')
        self.left_arrow = extract_bitmaps(iconpath + 'left_2c.gif')
        self.right_arrow = extract_bitmaps(iconpath + 'right_2c.gif')
        self.add_icon = icon('add_box48.png')
        self.add_box_icon = icon('add_box24.png')
        self.settings_icon = icon('settings48.png')
        self.settings_pixmap = pixmap('settings48.png')
        self.triangle_icon = icon('triangle48.png')
        self.triangle_close_icon = icon('triangle_close48.png')
        self.font_icon = icon('text_format48.png')
        self.kataja_icon = icon('kataja.png')

    def update(self, preferences, running_environment):
        """

        :param preferences:
        """
        self.prepare_fonts(preferences.fonts, running_environment)
        self.prepare_easing_curve(preferences.curve, preferences.move_frames)
        self.toggle_large_ui_font(preferences.large_ui_text, preferences.fonts)


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
        # self.easing_curve = [(1.0 / self.move_frames) + (float(x) /
        # self.move_frames) - curve.valueForProgress(float(x) /
        # self.move_frames) for x in range(self.move_frames)]
        # self.easing_curve=[(float(
        # x)/self.move_frames)-curve.valueForProgress(float(
        # x)/self.move_frames) for x in range(self.move_frames)]
        s = sum(self.easing_curve)
        self.easing_curve = [x / s for x in self.easing_curve]

    def prepare_fonts(self, fonts_dict, running_environment):
        """


        :param preferences:
        :param fonts_dict:
        :param fontdb:
        """
        # print('preparing fonts...')
        self.fonts = {}
        for key, font_tuple in fonts_dict.items():
            name, style, size = font_tuple
            size = int(size)
            font = self.fontdb.font(name, style, size)
            # print(name, font.exactMatch())
            if name == 'Asana Math' and not font.exactMatch():
                self.fontdb.addApplicationFont(
                    running_environment.resources_path + "Asana-Math.otf")
                font = self.fontdb.font(name, style, size)
            if style == 'Italic':
                font.setItalic(True)
            self.fonts[key] = font
        font = QtGui.QFontMetrics(self.fonts[MAIN_FONT])  # it takes 2 seconds to get FontMetrics
        # print('font leading: %s font height: %s ' % (font.leading(),
        # font.height()))
        main = self.fonts[MAIN_FONT]
        main.setHintingPreference(QtGui.QFont.PreferNoHinting)
        self.font_space_width = font.width(' ')
        self.font_bracket_width = font.width(']')
        self.font_bracket_height = font.height()
        # print('font metrics: ', font)
        # print(self.font_space_width, self.font_bracket_width,
        # self.font_bracket_height)
        self.fonts[SMALL_CAPS].setCapitalization(QtGui.QFont.SmallCaps)

    def toggle_large_ui_font(self, enabled, fonts_dict):
        ui_font = self.fonts[UI_FONT]
        console_font = self.fonts[CONSOLE_FONT]
        if enabled:
            if ui_font.pointSize() < 14:
                ui_font.setPointSize(14)
            if console_font.pointSize() < 14:
                console_font.setPointSize(14)
        else:
            ui_font.setPointSize(fonts_dict[UI_FONT][2])
            console_font.setPointSize(fonts_dict[CONSOLE_FONT][2])
    ### Font helper ###

    def font(self, name):
        """

        :param name:
        :return:
        """
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
