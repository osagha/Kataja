# coding=utf-8
import math

from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.Saved import Saved, SavedField
from kataja.singletons import ctrl, qt_prefs
from kataja.saved.movables.Node import Node

points = 36


class Amoeba(Saved, QtWidgets.QGraphicsObject):

    short_name = 'Group'

    def __init__(self, selection=None, persistent=True):
        Saved.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.ui_key = self.save_key + '_ui'
        self.host = None # not used, it is here because it is expected for UI elements
        self.selection = []
        self.selection_with_children = []
        self.persistent = persistent
        self._skip_this = not persistent
        self._selected = False
        self.points = []
        self.center_point = None
        self.outline = False
        self.fill = True
        self.color_key = ''
        self.color = None
        self.color_tr = None
        self.color_tr_tr = None
        self.path = None
        self.label_text = ''
        self.label_item = None
        self.include_children = False
        self.allow_overlap = True
        self._br = None
        self.selectable = persistent
        self.clickable = False
        self.draggable = False
        if selection:
            self.update_selection(selection)
        self.update_shape()
        self.update_colors()

    def __contains__(self, item):
        return item in self.selection_with_children

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65550

    def after_init(self):
        self.update_selection(self.selection)
        self.update_shape()
        self.update_colors()

    def after_model_update(self, changed_fields, transition_type):
        if changed_fields:
            self.update_selection(self.selection)
            self.update_shape()
            self.update_colors()

    def copy_from(self, source):
        """ Helper method to easily make a similar selection with different identity
        :param source:
        :return:
        """
        self.selection = source.selection
        self.selection_with_children = source.selection_with_children
        self.points = list(source.points)
        self.center_point = source.center_point
        self.outline = source.outline
        self.fill = source.fill
        self.color_key = source.color_key
        self.color = source.color
        self.color_tr = source.color_tr
        self.color_tr_tr = source.color_tr_tr
        self.path = source.path
        self.set_label_text(source.label_text)
        self.include_children = source.include_children
        self.allow_overlap = source.allow_overlap

    def set_label_text(self, text):
        self.label_text = text
        if text:
            if not self.label_item:
                self.label_item = QtWidgets.QGraphicsSimpleTextItem(text, self)
                f = QtGui.QFont(qt_prefs.font(g.SMALL_CAPS))
                f.setPointSize(f.pointSizeF()*2)
                self.label_item.setFont(f)
                self.label_item.setPen(qt_prefs.no_pen)
                self.label_item.setBrush(self.color)
            else:
                self.label_item.setText(text)
        else:
            if self.label_item:
                self.label_item.scene().removeItem(self.label_item)
                self.label_item = None

    def remove_node(self, node):
        """ Manual removal of single node, should be called e.g. when node is deleted.
        :param node:
        :return:
        """
        if node in self.selection:
            self.poke('selection')
            self.selection.remove(node)
        if node in self.selection_with_children:
            self.selection_with_children.remove(node)

        if self.selection:
            self.update_shape()
        else:
            if self.persistent:
                ctrl.forest.remove_group(self)
            else:
                ctrl.ui.remove_ui_for(self)

    def add_node(self, node):
        """ Manual addition of single node
        :param node:
        :return:
        """
        if node not in self.selection:
            self.poke('selection')
            self.selection.append(node)
            self.update_selection(self.selection)
            self.update_shape()

    def update_selection(self, selection):
        swc = []
        other_selections = set()
        if not self.allow_overlap:
            for amoeba in ctrl.forest.groups.values():
                other_selections = other_selections | set(amoeba.selection_with_children)

        def recursive_add_children(i):
            if isinstance(i, Node) and i not in swc and \
                    (i in selection or i not in other_selections):
                swc.append(i)
                for child in i.get_all_children():
                    recursive_add_children(child)

        if selection:
            self.selection = [item for item in selection if isinstance(item, Node) and
                              item.can_be_in_groups]
            if self.include_children:
                for item in self.selection:
                    recursive_add_children(item)
                self.selection_with_children = swc
            else:
                self.selection_with_children = self.selection
        else:
            self.selection = []
            self.selection_with_children = []

    def update_shape(self):

        def embellished_corners(item):
            x1, y1, x2, y2 = item.sceneBoundingRect().getCoords()
            corners = [(x1 - 5, y1 - 5),
                       (x2 + 5, y1 - 5),
                       (x2 + 5, y2 + 5),
                       (x1 - 5, y2 + 5)]

            return x1, y1, x2, y2, corners
        sel = [x for x in self.selection_with_children if x.isVisible()]

        if len(sel) == 0:
            self._br = QtCore.QRectF()
            self.path = None
            self.center_point = None
            return
        elif len(sel) == 1:
            x1, y1, x2, y2, route = embellished_corners(sel[0])
            self._br = QtCore.QRectF(x1 - 5, y1 - 5, x2 - x1 + 10, y2 - y1 + 10)
            self.path = QtGui.QPainterPath(QtCore.QPointF(route[0][0], route[0][1]))
            for x, y in route[1:]:
                self.path.lineTo(x, y)
            self.path.closeSubpath()
            center = self._br.center()
            self.center_point = center.x(), center.y()
            cx, cy = self.center_point

        else:
            corners = []
            c = 0
            x_sum = 0
            y_sum = 0
            min_x = 50000
            max_x = -50000
            min_y = 50000
            max_y = -50000
            for item in sel:
                c += 2
                x1, y1, x2, y2, icorners = embellished_corners(item)
                x_sum += x1
                x_sum += x2
                y_sum += y1
                y_sum += y2
                if x1 < min_x:
                    min_x = x1
                if x2 > max_x:
                    max_x = x2
                if y1 < min_y:
                    min_y = y1
                if y2 > max_y:
                    max_y = y2
                corners += icorners
            self.prepareGeometryChange()
            self._br = QtCore.QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            self.center_point = cx, cy
            r = max(max_x - min_x, max_y - min_y) * 1.1
            dots = 32
            step = 2 * math.pi / dots
            deg = 0
            route = []
            for n in range(0, dots):
                cpx = math.cos(deg)*r + cx
                cpy = math.sin(deg)*r + cy
                deg += step
                closest = None
                closest_d = 200000
                for px, py in corners:
                    d = (px - cpx) ** 2 + (py - cpy) ** 2
                    if d < closest_d:
                        closest = px, py
                        closest_d = d
                if closest:
                    if route:
                        last = route[-1]
                        if last == closest:
                            continue
                    route.append(closest)

        if self.label_item:
            label_width = self.label_item.boundingRect().width()
            label_height = self.label_item.boundingRect().height()
            label_center_x, label_center_y = label_width / 2, label_height / 2

            min_dist = 100000
            prev_x, prev_y = route[-1]
            best_x, best_y = 0, 0
            for x, y in route:
                mx = (prev_x + x) / 2
                my = (prev_y + y) / 2
                d = (cx - mx) ** 2 + (cy - my) ** 2
                if d < min_dist:
                    if mx < cx:
                        mx -= label_width + 2
                    else:
                        mx += 2
                    if my < cy:
                        my -= label_height + 2
                    else:
                        my += 2
                    items = ctrl.graph_scene.items(QtCore.QPointF(mx + label_center_x,
                                                   my + label_center_y)) + \
                            ctrl.graph_scene.items(QtCore.QPointF(mx + (label_center_x * 0.80),
                                                   my + label_center_y)) + \
                            ctrl.graph_scene.items(QtCore.QPointF(mx + (label_center_x * 0.20),
                                                   my + label_center_y))
                    collision = False
                    for item in items:
                        if isinstance(item, (Node, Amoeba)):
                            collision = True
                            break
                    if not collision:
                        min_dist = d
                        best_x, best_y = mx, my
                prev_x, prev_y = x, y
            self.label_item.setPos(best_x, best_y)
        curved_path = Amoeba.interpolate_point_with_bezier_curves(route)
        sx, sy = route[0]
        self.path = QtGui.QPainterPath(QtCore.QPointF(sx, sy))
        for fx, fy, sx, sy, ex, ey in curved_path:
            self.path.cubicTo(fx, fy, sx, sy, ex, ey)
        # This is costly
        if True:
            for item in self.collidingItems():
                if isinstance(item, Node) and item not in self.selection_with_children:
                    x, y = item.current_scene_position
                    subshape = item.shape().translated(x, y)
                    subshape_points = []
                    for i in range(0, subshape.elementCount()):
                        element = subshape.elementAt(i)
                        subshape_points.append((element.x, element.y))
                    curved_path = Amoeba.interpolate_point_with_bezier_curves(subshape_points)
                    sx, sy = subshape_points[0]
                    subshape = QtGui.QPainterPath(QtCore.QPointF(sx, sy))
                    for fx, fy, sx, sy, ex, ey in curved_path:
                        subshape.cubicTo(fx, fy, sx, sy, ex, ey)

                    self.path = self.path.subtracted(subshape)

    def shape(self):
        if self.path:
            return self.path
        else:
            return QtGui.QPainterPath()

    def update_position(self):
        self.update_shape()

    def clockwise_path_points(self, margin=2):
        """ Return points along the path circling the group. A margin can be provided to make the
        points be n points away from the path. Points start from the topmost, rightmost point.
        :param margin:
        :return:
        """
        if not self.path:
            return QtCore.QPointF(0, 0)  # hope this group will be removed immediately
        max_x = -30000
        min_y = 30000
        start_i = 0
        ppoints = []
        cx, cy = self.center_point
        better_path = [] # lets have not only corners, but also points along the edges
        last_element = self.path.elementAt(self.path.elementCount()-1)
        last_x = last_element.x
        last_y = last_element.y
        for i in range(0, self.path.elementCount()):
            element = self.path.elementAt(i)
            x = element.x
            y = element.y
            better_path.append(((last_x + x) / 2, (last_y + y) / 2))
            better_path.append((x, y))
            last_x = x
            last_y = y

        for i, (x, y) in enumerate(better_path):
            if margin != 0:
                dx = x - cx
                dy = y - cy
                d = math.hypot(dx, dy)
                change = (d + margin) / d  # should return values like 1.08
                x = cx + (dx * change)
                y = cy + (dy * change)
            ppoints.append((x, y))
            if y < min_y or (y == min_y and x > max_x):
                min_y = y
                max_x = x
                start_i = i
        return ppoints[start_i:] + ppoints[:start_i]

    def boundingRect(self):
        if not self._br:
            self.update_shape()
        return self._br

    def get_color_id(self):
        return self.color_key

    def update_colors(self, color_key=''):
        if not self.color_key:
            self.color_key = color_key or "accent1"
        elif color_key:
            self.color_key = color_key
        self.color = ctrl.cm.get(self.color_key)
        self.color_tr = ctrl.cm.get(self.color_key + 'tr')
        self.color_tr_tr = QtGui.QColor(self.color)
        self.color_tr_tr.setAlphaF(0.2)
        if self.label_item:
            self.label_item.setBrush(self.color)

    def select(self, event=None, multi=False):
        """ Scene has decided that this node has been clicked
        :param event:
        :param multi: assume multiple selection (append, don't replace)
        """
        ctrl.multiselection_start()
        if (event and event.modifiers() == QtCore.Qt.ShiftModifier) or multi:
            # multiple selection
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
                for item in self.selection:
                    ctrl.add_to_selection(item)
        elif ctrl.is_selected(self):
            ctrl.deselect_objects()
        else:
            ctrl.deselect_objects()
            ctrl.add_to_selection(self)
            for item in self.selection:
                ctrl.add_to_selection(item)
        ctrl.multiselection_end()

    def update_selection_status(self, value):
        """

        :param value:
        :return:
        """
        self._selected = value

    def paint(self, painter, style, QWidget_widget=None):
        if self.selection and self.path:
            if self.fill:
                painter.fillPath(self.path, self.color_tr_tr)
            if self._selected:
                painter.setPen(ctrl.cm.selection())
                painter.drawPath(self.path)
            elif self.outline:
                painter.setPen(self.color)
                painter.drawPath(self.path)


    @staticmethod
    def interpolate_point_with_bezier_curves(points):
        """ Curved path algorithm based on example by Raul Otaño Hurtado, from
        http://www.codeproject.com/Articles/769055/Interpolate-D-points-usign-Bezier-curves-in-WPF
        :param points:
        :return:
        """
        if len(points) < 3:
            return None
        res = []

        # if is close curve then add the first point at the end
        if points[-1] != points[0]:
            points.append(points[0])

        for i, (x1, y1) in enumerate(points[:-1]):
            if i == 0:
                x0, y0 = points[-2]
            else:
                x0, y0 = points[i - 1]
            x2, y2 = points[i + 1]
            if i == len(points) - 2:
                x3, y3 = points[1]
            else:
                x3, y3 = points[i + 2]

            xc1 = (x0 + x1) / 2.0
            yc1 = (y0 + y1) / 2.0
            xc2 = (x1 + x2) / 2.0
            yc2 = (y1 + y2) / 2.0
            xc3 = (x2 + x3) / 2.0
            yc3 = (y2 + y3) / 2.0
            len1 = math.hypot(x1 - x0, y1 - y0)
            len2 = math.hypot(x2 - x1, y2 - y1)
            len3 = math.hypot(x3 - x2, y3 - y2)

            k1 = len1 / (len1 + len2)
            k2 = len2 / (len2 + len3)

            xm1 = xc1 + (xc2 - xc1) * k1
            ym1 = yc1 + (yc2 - yc1) * k1

            xm2 = xc2 + (xc3 - xc2) * k2
            ym2 = yc2 + (yc3 - yc2) * k2

            smooth = 0.8
            ctrl1_x = xm1 + (xc2 - xm1) * smooth + x1 - xm1
            ctrl1_y = ym1 + (yc2 - ym1) * smooth + y1 - ym1
            ctrl2_x = xm2 + (xc2 - xm2) * smooth + x2 - xm2
            ctrl2_y = ym2 + (yc2 - ym2) * smooth + y2 - ym2
            res.append((ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, x2, y2))
        return res

    selection = SavedField("selection")
    color_key = SavedField("color_key")
    label_text = SavedField("label_text")
    include_children = SavedField("include_children")
    allow_overlap = SavedField("allow_overlap")
    fill = SavedField("fill")
    outline = SavedField("outline")
    persistent = SavedField("persistent")