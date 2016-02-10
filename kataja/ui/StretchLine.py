# coding=utf-8
# #######################################################
from PyQt5 import QtWidgets

from kataja.shapes import draw_arrow_shape, arrow_shape_bounding_rect


class StretchLine(QtWidgets.QGraphicsLineItem):
    """ Temporary arrow for dragging and pointing """

    def __init__(self, line, ui_key, host):
        self._arrow_size = 5.0
        self.setZValue(52)
        self.ui_key = ui_key
        self.host = host
        QtWidgets.QGraphicsLineItem.__init__(self, line)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65655

    def remove(self):
        """


        """
        del self
        # self.removeFromIndex()

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        draw_arrow_shape(self, painter)

    def boundingRect(self):
        """


        :return:
        """
        return arrow_shape_bounding_rect(self)

    def update_visibility(self):
        """


        """
        self.show()

