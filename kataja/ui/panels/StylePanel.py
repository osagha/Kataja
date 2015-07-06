from PyQt5 import QtWidgets, QtCore

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor, QStandardItem
from kataja.Node import Node
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.ui.OverlayButton import PanelButton
from kataja.ui.panels.field_utils import find_list_item, add_and_select_ambiguous_marker, \
    remove_ambiguous_marker, TableModelComboBox, ColorSelector, set_value, mini_button, font_button
from utils import time_me

__author__ = 'purma'

scope_display_order = [g.SELECTION, g.CONSTITUENT_EDGE, g.FEATURE_EDGE, g.GLOSS_EDGE, g.ARROW, g.PROPERTY_EDGE,
                       g.ATTRIBUTE_EDGE, g.ABSTRACT_EDGE]

scope_display_items = {
    g.SELECTION: 'Current selection',
    g.CONSTITUENT_NODE: 'Constituents',
    g.FEATURE_NODE: 'Features',
    g.GLOSS_NODE: 'Glosses',
    g.ARROW: 'Arrows',
    g.PROPERTY_NODE: 'Properties',
    g.ATTRIBUTE_NODE: 'Attributes',
    g.ABSTRACT_NODE: 'Unspecified nodes'
}


line_icons = {

}


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, panel):
        self.shape_key = shape_key
        self.engine = DrawnIconEngine(SHAPE_PRESETS[shape_key]['icon'], owner=self)
        QIcon.__init__(self, self.engine)
        self.panel = panel
        # pixmap = QPixmap(60, 20)
        # pixmap.fill(ctrl.cm.ui())
        # self.addPixmap(pixmap)

    def paint_settings(self):
        s = SHAPE_PRESETS[self.shape_key]
        pen = self.panel.edge_color_selector.currentData()
        if not pen:
            pen = 'content1'
        d = {'color': ctrl.cm.get(pen)}
        return d


class ShapeSelector(TableModelComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(64, 16))
        # self.shape_selector.setView(view)
        items = []

        for lt in SHAPE_PRESETS.keys():
            item = QStandardItem(LineStyleIcon(lt, parent), '')
            item.setData(lt)
            item.setToolTip(lt)
            item.setSizeHint(QSize(64, 16))
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)


class StylePanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        # layout.setContentsMargins(4, 4, 4, 4)
        self.scope = g.CONSTITUENT_NODE
        self.base_scope = g.CONSTITUENT_NODE
        self._nodes_in_selection = []
        self._edges_in_selection = []
        self.cached_node_types = set()
        self.current_color = ctrl.cm.drawing()
        self.watchlist = ['edge_shape', 'edge_color', 'selection_changed', 'forest_changed']
        # Other items may be temporarily added, they are defined as class.variables

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        label = QtWidgets.QLabel('Style for', self)
        hlayout.addWidget(label)
        self.scope_selector = QtWidgets.QComboBox(self)
        self.scope_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.scope_selector.setMinimumWidth(120)
        ui_manager.connect_element_to_action(self.scope_selector, 'style_scope')
        hlayout.addWidget(self.scope_selector, 1, QtCore.Qt.AlignLeft)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        default_font = qt_prefs.font(g.MAIN_FONT)
        self.font_selector = font_button(ui_manager, hlayout, default_font, 'font_selector')

        self.node_color_selector = ColorSelector(self)
        ui_manager.connect_element_to_action(self.node_color_selector, 'change_node_color')
        hlayout.addWidget(self.node_color_selector, 1, QtCore.Qt.AlignLeft)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.shape_selector = ShapeSelector(self)
        ui_manager.connect_element_to_action(self.shape_selector, 'change_edge_shape')
        hlayout.addWidget(self.shape_selector, 1, QtCore.Qt.AlignLeft)

        self.font_selector.setMinimumWidth(self.shape_selector.width())
        self.font_selector.setMaximumWidth(self.shape_selector.width())

        self.edge_color_selector = ColorSelector(self)
        ui_manager.connect_element_to_action(self.edge_color_selector, 'change_edge_color')
        hlayout.addWidget(self.edge_color_selector, 1, QtCore.Qt.AlignLeft)

        self.edge_options = PanelButton(qt_prefs.settings_icon, text='More line options',
                                        parent=self, size=16)
        self.edge_options.setCheckable(True)
        ui_manager.connect_element_to_action(self.edge_options, 'toggle_line_options')
        hlayout.addWidget(self.edge_options, 1, QtCore.Qt.AlignRight)
        layout.addLayout(hlayout)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use selection as scope
        :return:
        """
        self._edges_in_selection = []
        self._nodes_in_selection = []
        self.cached_node_types = set()
        if ctrl.selected:
            if self.scope != g.SELECTION:
                self.base_scope = self.scope
            self.scope = g.SELECTION
            for item in ctrl.selected:
                if isinstance(item, Node):
                    self._nodes_in_selection.append(item)
                    self.cached_node_types.add(item.node_type)
                elif isinstance(item, Edge):
                    self._edges_in_selection.append(item)
        elif self.base_scope:
            self.scope = self.base_scope
        self.update_scope_selector_options(selection_changed=True)
        i = find_list_item(self.scope, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_color(self, color):
        self.current_color = color
        self.color_selector.select_data(color)
        self.color_selector.update()
        self.shape_selector.update()

    def update_color_from(self, source):
        if source == 'node_color':
            s = self.node_color_selector
            m = s.model()
            prev_color = m.selected_color
            color_id = s.currentData()
            m.selected_color = color_id
            if (not color_id) or (not ctrl.cm.get(color_id)) or prev_color == color_id:
                ctrl.ui.start_color_dialog(s, self, 'node_color', color_id)
                return
            if self.scope == g.SELECTION:
                for node in ctrl.selected:
                    if isinstance(node, Node):
                        node.color_id = color_id
                        node.update()
            elif self.scope:
                ctrl.forest.settings.node_settings(self.scope, 'color', color_id)
            s.select_data(color_id)
            s.update()
            return color_id
        elif source == 'edge_color':
            s = self.edge_color_selector
            m = s.model()
            prev_color = m.selected_color
            color_id = s.currentData()
            m.selected_color = color_id
            if (not color_id) or (not ctrl.cm.get(color_id)) or prev_color == color_id:
                ctrl.ui.start_color_dialog(s, self, 'edge_color', color_id)
                return
            if self.scope == g.SELECTION:
                for edge in ctrl.selected:
                    if isinstance(edge, Edge):
                        edge.color_id = color_id
                        edge.update()
            elif self.scope:
                edge_type = ctrl.forest.settings.node_settings(self.scope, 'edge')
                ctrl.forest.settings.edge_type_settings(edge_type, 'color', color_id)
            s.select_data(color_id)
            s.update()
            self.shape_selector.update()
            return color_id


    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has
        otherwise changed.
        :return:
        """
        self.update_fields()

    # @time_me
    def update_scope_selector_options(self, selection_changed=False):
        """ Redraw scope selector, show only scopes that are used in this forest """
        scope_list = [x for x in scope_display_order if x in self.cached_node_types]
        self.scope_selector.clear()
        if self._nodes_in_selection or self._edges_in_selection:
            self.scope_selector.addItem(scope_display_items[g.SELECTION], g.SELECTION)
        if not scope_list:
            self.scope_selector.addItem(scope_display_items[g.CONSTITUENT_NODE],
                                        g.CONSTITUENT_NODE)
        for item in scope_list:
            self.scope_selector.addItem(scope_display_items[item], item)

    def update_fields(self):
        """ Update different fields in the panel to show the correct values based on selection
        or current scope. There may be that this makes fields to remove or add new values to
        selectors or do other hard manipulation to fields.

        First find what are the properties of the selected edges.
        If they are conflicting, e.g. there are two different colors in selected edges, they cannot
         be shown in the color selector. They can still be overridden with new selection.
        """
        if self.scope == g.SELECTION:
            d = self.build_display_values()
            for key, item in d.items():
                value, enabled, conflict = item
                if key == 'edge_color':
                    f = self.edge_color_selector
                elif key == 'node_color':
                    f = self.node_color_selector
                elif key == 'node_font':
                    f = self.font_selector
                elif key == 'edge_shape':
                    f = self.shape_selector
                else:
                    continue
                set_value(f, value, conflict=conflict, enabled=enabled)
        else:
            ns = ctrl.forest.settings.node_settings
            es = ctrl.forest.settings.edge_type_settings
            edge_scope = ns(self.scope, 'edge')
            node_color = ns(self.scope, 'color')
            node_font = ns(self.scope, 'font')
            edge_color = es(edge_scope, 'color')
            edge_shape = es(edge_scope, 'shape_name')
            # Color selector - show
            set_value(self.node_color_selector, node_color, False)
            set_value(self.font_selector, node_font, False)
            set_value(self.edge_color_selector, edge_color, False)
            set_value(self.shape_selector, edge_shape, False)
            #self.current_color = edge_color

    def build_display_values(self):
        d = {}
        if len(self._edges_in_selection) + len(self._nodes_in_selection) == 1:
            if self._edges_in_selection:
                e = self._edges_in_selection[0]
                d['edge_color'] = (e.color_id, True, False)
                d['edge_shape'] = (e.shape_name, True, False)
                d['node_color'] = ('', False, False)
                d['node_font'] = ('', False, False)
            elif self._nodes_in_selection:
                n = self._nodes_in_selection[0]
                d['edge_color'] = ('', False, False)
                d['edge_shape'] = ('', False, False)
                d['node_color'] = (n.color_id, True, False)
                d['node_font'] = (n.font, True, False)
        else:
            color_conflict = False
            shape_conflict = False
            color = None
            shape = None
            for e in self._edges_in_selection:
                if not color:
                    color = e.color_id
                elif e.color_id != color:
                    color_conflict = True
                if not shape:
                    shape = e.shape_name
                elif e.shape_name != shape:
                    shape_conflict = True
            ncolor_conflict = False
            font_conflict = False
            ncolor = None
            font = None
            for n in self._nodes_in_selection:
                if not ncolor:
                    ncolor = n.color_id
                elif n.color_id != ncolor:
                    ncolor_conflict = True
                if not font:
                    font = n.font
                elif n.font != font:
                    font_conflict = True
            d['edge_color'] = (color, bool(color), color_conflict)
            d['edge_shape'] = (shape, bool(shape), shape_conflict)
            d['node_color'] = (ncolor, bool(ncolor), ncolor_conflict)
            d['node_font'] = (font, bool(font), font_conflict)
        return d

    @time_me
    def update_fields_old(self):
        """ Update different fields in the panel to show the correct values based on selection
        or current scope. There may be that this makes fields to remove or add new values to
        selectors or do other hard manipulation to fields.

        First find what are the properties of the selected edges.
        If they are conflicting, e.g. there are two different colors in selected edges, they cannot
         be shown in the color selector. They can still be overridden with new selection.
        """
        edge_shape = None
        edge_color = None
        ambiguous_edge = False
        ambiguous_color = False
        ambiguous_type = False
        edge_type = None

        if self.scope == g.SELECTION:
            edges = []
            for item in ctrl.selected:
                if isinstance(item, Edge):
                    edges.append(item)
            if len(edges) == 0:
                return
            if len(edges) == 1:
                e = edges[0]
                edge_color = e.color_id
                edge_shape = e.shape_name
                edge_type = e.edge_type
            else:
                for edge in edges:
                    if not edge_shape:
                        edge_shape = edge.shape_name
                    elif edge.shape_name != edge_shape:
                        ambiguous_edge = True
                    if not edge_color:
                        edge_color = edge.color_id
                    elif edge.color_id != edge_color:
                        ambiguous_color = True
                    if not edge_type:
                        edge_type = edge.edge_type
                    elif edge.edge_type != edge_type:
                        ambiguous_type = True
            if edge_type and not ambiguous_type:
                self.color_selector.default_color = ctrl.forest.settings.edge_type_settings(
                    edge_type, 'color')
            else:
                self.color_selector.default_color = None
        else:
            edge_color = ctrl.forest.settings.edge_type_settings(self.scope, 'color')
            edge_shape = ctrl.forest.settings.edge_type_settings(self.scope, 'shape_name')
        # Color selector - show
        set_value(self.color_selector, edge_color, ambiguous_color)
        self.current_color = edge_color
        # Shape selector -show shape of selected edges, or '---' if they contain more than 1 shape.
        set_value(self.shape_selector, edge_shape, ambiguous_edge)
        self.shape_selector.update()

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        #print('StylePanel alerted: ', obj, signal, field_name, value)
        if signal == 'selection_changed':
            self.update_selection()
            self.update_fields()
        elif signal == 'forest_changed':
            self.update_selection()
            self.update_fields()






