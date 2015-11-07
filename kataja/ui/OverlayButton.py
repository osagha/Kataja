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

from kataja.errors import UIError
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g

borderstyle = """
PanelButton {border: 1px transparent none}
:hover {border: 1px solid %s; border-radius: 3}
:pressed {border: 2px solid %s; border-radius: 3}
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
        self.setContentsMargins(0, 0, 0, 0)
        self.setFlat(True)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        if self.pixmap:
            image = self.pixmap.toImage()
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()
        elif self.draw_method:
            size = self.iconSize()

            hidp = self.devicePixelRatio()
            isize = QtCore.QSize(size.width() * hidp, size.height() * hidp)

            image = QtGui.QImage(
                isize, QtGui.QImage.Format_ARGB32_Premultiplied)
            image.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(c)
            self.draw_method(painter, image.rect(), c)
            painter.end()

        i = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
        self.setIcon(i)
        self.setStyleSheet(borderstyle % (c.name(), c.lighter().name()))

    def update_color(self):
        self.compose_icon()

    def event(self, e):
        if e.type() == QtCore.QEvent.PaletteChange:
            self.compose_icon()
        return QtWidgets.QPushButton.event(self, e)


class OverlayButton(PanelButton):
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

    def __init__(self, pixmap, host, role, ui_key, text=None, parent=None,
                 size=16, color_key='accent8', draw_method=None, **kwargs):
        super().__init__(pixmap, text=text, parent=parent, size=size,
                         color_key=color_key, draw_method=draw_method)
        self.host = host
        self.ui_key = ui_key
        self.role = role
        self.edge = None
        # self.setCursor(Qt.PointingHandCursor)

    def update_position(self):
        """


        :raise UIError:
        """
        if not self.host:
            return

        if self.role == g.REMOVE_MERGER:
            adjust = QtCore.QPointF(19, -self.host.height / 2)
            if not self.edge:
                edges = [x for x in self.host.edges_down if
                         x.edge_type is g.CONSTITUENT_EDGE and
                         x.end.is_placeholder()]
                if not edges:
                    raise UIError(
                        "Remove merger suggested for merger with no children")
                else:
                    self.edge = edges[0]
            p = QtCore.QPointF(self.edge.start_point[0],
                               self.edge.start_point[1])
            p = ctrl.main.graph_view.mapFromScene(p) + adjust
            p = p.toPoint()
        elif self.role == g.START_CUT:
            adjust = QtCore.QPointF(self.host.end.width / 2,
                                    self.host.end.height / 2)
            p = ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(self.host.start_point[0],
                               self.host.start_point[1]) + adjust)
        elif self.role == g.END_CUT:
            if self.host.alignment == g.LEFT:
                adjust = QtCore.QPointF(-self.host.end.width / 2,
                                        -self.host.end.height / 2)
            else:
                adjust = QtCore.QPointF(self.host.end.width / 2,
                                        -self.host.end.height / 2)
            p = ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(self.host.start_point[0],
                               self.host.start_point[1]) + adjust)
        elif self.role == g.ADD_TRIANGLE:
            x, y, z = self.host.current_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2))
            p -= QtCore.QPoint((self.iconSize().width() / 2) + 4, 0)
        elif self.role == g.REMOVE_TRIANGLE:
            x, y, z = self.host.current_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2))
            p -= QtCore.QPoint((self.iconSize().width() / 2) + 4, 0)
        else:
            raise UIError(
                "Unknown role for OverlayButton, don't know where to put it.")
        self.move(p)

    def enterEvent(self, event):
        if self.role == g.REMOVE_MERGER:
            self.host.hovering = True
        PanelButton.enterEvent(self, event)

    def leaveEvent(self, event):
        if self.role == g.REMOVE_MERGER:
            self.host.hovering = False
        PanelButton.leaveEvent(self, event)
