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

from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.UIItem import UIItem
from kataja.errors import UIError
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_items.TouchArea import TouchArea

borderstyle = """
PanelButton {border: 1px transparent none}
:hover {border: 1px solid %s; border-radius: 3}
:pressed {border: 2px solid %s; background-color: %s; border-radius: 3}
:checked {border: 1px solid %s; background-color: %s; border-radius: 3}
"""


class PanelButton(QtWidgets.QPushButton):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by
        setting
        TwoColorIconEngine for normal button, but let's keep this in case we
        need to deliver
        palette updates to icon engines.
        PanelButtons are to be contained in panels or other widgets,
        they cannot be targeted
        individually.
     """

    def __init__(self, pixmap, text=None, parent=None, size=16,
                 color_key='accent8', draw_method=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self.draw_method = draw_method
        self.color_key = color_key
        if not (pixmap or draw_method):
            raise TypeError('Button needs either pixmap/icon or draw_method')
        if isinstance(size, QtCore.QSize):
            width = size.width()
            height = size.height()
        elif isinstance(size, tuple):
            width = size[0]
            height = size[1]
        else:
            width = size
            height = size
        size = QtCore.QSize(width, height)
        self.setIconSize(size)
        if isinstance(pixmap, str):
            pixmap = getattr(qt_prefs, pixmap)
        if isinstance(pixmap, QtGui.QIcon):
            self.pixmap = pixmap.pixmap(size)
        else:
            self.pixmap = pixmap
        self.compose_icon()
        if text:
            if ctrl.main.use_tooltips:
                self.setToolTip(text)
            self.setStatusTip(text)
        self.w2 = self.iconSize().width() / 2
        self.h2 = self.iconSize().height() / 2
        self.setContentsMargins(0, 0, 0, 0)
        self.setFlat(True)

    def contextual_color(self):
        if self.isDown():
            return ctrl.cm.get(self.color_key).lighter()
        else:
            return ctrl.cm.get(self.color_key)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        paper = ctrl.cm.paper()
        paper2 = ctrl.cm.paper2()
        if self.pixmap:
            image = self.pixmap.toImage()
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()
        elif self.draw_method:
            size = self.iconSize()
            #hidp = self.devicePixelRatio()
            isize = QtCore.QSize(size.width() * 2, size.height() * 2)

            image = QtGui.QImage(
                isize, QtGui.QImage.Format_ARGB32_Premultiplied)
            image.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(image)
            #painter.setDevicePixelRatio(2.0)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(c)
            self.draw_method(painter, image.rect(), c)
            painter.end()

        i = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
        self.setIcon(i)
        self.setStyleSheet(borderstyle % (c.name(), c.lighter().name(), paper.name(), c.name(),
                                          paper2.name()))

    def update_colors(self):
        self.compose_icon()

    def event(self, e):
        if e.type() == QtCore.QEvent.PaletteChange:
            self.compose_icon()
        return QtWidgets.QPushButton.event(self, e)


class OverlayButton(UIItem, PanelButton):
    """ A floating button on top of main canvas. These are individual UI
    elements each.

    :param pixmap:
    :param host:
    :param role:
    :param ui_key:
    :param text:
    :param parent:
    :param size:
    :param color_key:
    """

    def __init__(self, host, ui_key, pixmap, role, text=None, parent=None,
                 size=16, color_key='accent8', draw_method=None, **kwargs):
        UIItem.__init__(self, ui_key, host)
        PanelButton.__init__(self, pixmap, text=text, parent=parent, size=size,
                         color_key=color_key, draw_method=draw_method)
        self.role = role
        self.edge = None

    def update_position(self):
        """


        :raise UIError:
        """
        if not self.host:
            return

        if self.role == g.START_CUT:
            adjust = QtCore.QPointF(self.host.start.width - self.w2,
                                    self.host.start.height / 2 - self.h2)
            p = ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(self.host.start_point[0],
                               self.host.start_point[1]) + adjust)
        elif self.role == g.END_CUT:
            if self.host.alignment == g.LEFT:
                adjust = QtCore.QPointF(-self.host.end.width - self.w2,
                                        -self.host.end.height / 2- self.h2)
            else:
                adjust = QtCore.QPointF(self.host.end.width - self.w2,
                                        -self.host.end.height / 2 - self.h2)
            p = ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(self.host.end_point[0],
                               self.host.end_point[1]) + adjust)
        elif self.role == g.ADD_TRIANGLE:
            x, y = self.host.current_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2))
            p -= QtCore.QPoint(self.w2 + 4, 0)
        elif self.role == g.REMOVE_TRIANGLE:
            x, y = self.host.current_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2))
            p -= QtCore.QPoint(self.w2 + 4, 0)
        else:
            raise UIError(
                "Unknown role for OverlayButton, don't know where to put it.")
        self.move(p)


class RemoveMergerButton(OverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, ui_key, parent=None):

        super().__init__(host,
                         ui_key,
                         'delete_icon',
                         g.REMOVE_MERGER,
                         text='Remove this non-merging node',
                         parent=parent,
                         size=16,
                         color_key='accent8')
        self.role = g.REMOVE_MERGER
        self.action_name = 'remove_merger'
        self.edge = None

    def update_position(self):
        """ """
        x, y = self.host.current_scene_position
        p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x + self.host.width / 2,
                                                             y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)

class RemoveNodeButton(OverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, ui_key, parent=None):

        super().__init__(host,
                         ui_key,
                         'delete_icon',
                         g.REMOVE_NODE,
                         text='Remove node',
                         parent=parent,
                         size=16,
                         color_key='accent3')
        self.role = g.REMOVE_NODE
        self.action_name = 'remove_node'
        self.edge = None

    def update_position(self):
        """ """
        x, y = self.host.current_scene_position
        p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x + self.host.width / 2,
                                                             y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        self.move(p)

    def enterEvent(self, event):

        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)



class AmoebaOptionsButton(OverlayButton):

    def __init__(self, host, ui_key, parent=None):
        super().__init__(host,
                         ui_key,
                         qt_prefs.settings_pixmap,
                         g.AMOEBA_OPTIONS,
                         text='Name this selection',
                         parent=parent,
                         size=16,
                         color_key=host.color_key)
        self.role = g.AMOEBA_OPTIONS
        self.action_name = 'toggle_amoeba_options'
        self.edge = None

    def update_position(self):
        """ Tries to find an unoccupied position in the radius of the group """
        candidates = self.host.clockwise_path_points(8)
        if not candidates:
            return
        scene_size = ctrl.main.graph_view.mapToScene(self.width() / 2, self.height() / 2) - ctrl.main.graph_view.mapToScene(0, 0)
        w2 = scene_size.x()
        h2 = scene_size.y()
        for x, y in candidates:
            overlap = False
            items = ctrl.graph_scene.items(QtCore.QPointF(x - w2, y - h2))
            for item in items:
                if isinstance(item, TouchArea):
                    overlap = True
                    break
            if not overlap:
                break
        p = ctrl.main.graph_view.mapFromScene(x - w2, y - h2)
        self.move(p)


class NodeEditorButton(OverlayButton):

    def __init__(self, host, ui_key, parent=None):
        super().__init__(host,
                         ui_key,
                         qt_prefs.settings_pixmap,
                         g.NODE_EDITOR_BUTTON,
                         text='Edit this node',
                         parent=parent,
                         size=16,
                         color_key='accent8')
        self.role = g.NODE_EDITOR_BUTTON
        self.action_name = 'toggle_node_edit_embed'
        self.edge = None

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(9, -8)
        x, y = self.host.current_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        p = p.toPoint()
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


button_definitions = {g.REMOVE_MERGER: RemoveMergerButton,
                      g.AMOEBA_OPTIONS: AmoebaOptionsButton,
                      g.NODE_EDITOR_BUTTON: NodeEditorButton,
                      g.REMOVE_NODE: RemoveNodeButton}


def button_factory(role_key, node, save_key, parent):
    constructor = button_definitions[role_key]
    return constructor(node, save_key, parent)