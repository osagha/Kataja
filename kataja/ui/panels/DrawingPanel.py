from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap, QStandardItem

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.utils import time_me
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.ui.ColorSwatchIconEngine import ColorSwatchIconEngine
from kataja.ui.TwoColorButton import TwoColorButton


__author__ = 'purma'

scope_display_order = [g.SELECTION, g.CONSTITUENT_EDGE, g.FEATURE_EDGE, g.GLOSS_EDGE, g.ARROW, g.PROPERTY_EDGE, g.ATTRIBUTE_EDGE, g.ABSTRACT_EDGE]

scope_display_items = {
    g.SELECTION: 'Current selection',
    g.CONSTITUENT_EDGE: 'Constituent relations',
    g.FEATURE_EDGE: 'Feature relations',
    g.GLOSS_EDGE: 'Gloss relations',
    g.ARROW: 'Arrows',
    g.PROPERTY_EDGE: 'Property relations',
    g.ATTRIBUTE_EDGE: 'Attribute relatios',
    g.ABSTRACT_EDGE: 'Unspecified relations'
}

line_icons = {

}


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, panel):
        self.shape_key = shape_key
        self.engine = DrawnIconEngine(SHAPE_PRESETS[shape_key]['icon'], owner=self)
        QIcon.__init__(self, self.engine)
        self.panel = panel
        #pixmap = QPixmap(60, 20)
        #pixmap.fill(ctrl.cm.ui())
        #self.addPixmap(pixmap)


    def paint_settings(self):
        s = SHAPE_PRESETS[self.shape_key]
        pen = self.panel.current_color
        if not isinstance(pen, QColor):
            pen = ctrl.cm.get(pen)

        d = {'color':pen}
        return d

class LineColorIcon(QIcon):
    def __init__(self, color_id):
        QIcon.__init__(self, ColorSwatchIconEngine(color_id))


class ColorSelector(QtWidgets.QComboBox):

    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        self.setIconSize(QSize(16, 16))
        #self.color_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        model = self.model()
        model.setRowCount(8)
        model.setColumnCount(4)
        items = []
        for c in ctrl.cm.color_keys:
            item = QStandardItem(LineColorIcon(c), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            items.append(item)
        new_view = QtWidgets.QTableView()
        add_icon = QIcon()
        add_icon.fromTheme("list-add")
        add_item = QStandardItem('+')
        add_item.setTextAlignment(QtCore.Qt.AlignCenter)
        add_item.setSizeHint(QSize(22,20))
        table = [items[0:3], items[5:13], items[13:21], [add_item]]
        for c, column in enumerate(table):
            for r, item in enumerate(column):
                model.setItem(r, c, item)
        new_view.horizontalHeader().hide()
        new_view.verticalHeader().hide()
        new_view.setCornerButtonEnabled(False)
        new_view.setModel(model)
        new_view.resizeColumnsToContents()
        cw = new_view.columnWidth(0)
        new_view.setMinimumWidth(model.columnCount() * cw)
        self.setView(new_view)


class DrawingPanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        #layout.setContentsMargins(4, 4, 4, 4)
        self.scope = g.CONSTITUENT_EDGE
        self._old_scope = g.CONSTITUENT_EDGE
        self.scope_selector = QtWidgets.QComboBox(self)
        self.scope_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._visible_scopes = []
        self.current_color = ctrl.cm.drawing()
        ui_manager.ui_buttons['line_type_target'] = self.scope_selector
        # Other items may be temporarily added, they are defined as class.variables
        ui_manager.connect_selector_to_action(self.scope_selector, 'edge_shape_scope')
        layout.addWidget(self.scope_selector)

        self.shape_selector = QtWidgets.QComboBox(self)
        self.shape_selector.setIconSize(QSize(64, 16))
        self.shape_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        #self.shape_selector.setView(view)
        ui_manager.ui_buttons['line_type'] = self.shape_selector
        items = [('', LineStyleIcon(lt, self), lt) for lt in SHAPE_PRESETS.keys()]
        for text, icon, data in items:
            self.shape_selector.addItem(icon, text, data)
        ui_manager.connect_selector_to_action(self.shape_selector, 'change_edge_shape')
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        hlayout.addWidget(self.shape_selector)

        self.color_selector = ColorSelector(self)
        ui_manager.ui_buttons['line_color'] = self.color_selector
        ui_manager.connect_selector_to_action(self.color_selector, 'change_edge_color')
        hlayout.addWidget(self.color_selector)

        self.edge_options = QtWidgets.QPushButton('#', self)
        self.edge_options.setCheckable(True)
        self.edge_options.setMinimumSize(QSize(24, 24))
        self.edge_options.setMaximumSize(QSize(24, 24))
        ui_manager.ui_buttons['line_options'] = self.edge_options
        ui_manager.connect_button_to_action(self.edge_options, 'toggle_line_options')
        #self.edge_options.setFlat(True)
        hlayout.addWidget(self.edge_options)
        layout.addLayout(hlayout)




        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()


    @staticmethod
    def find_list_item(data, selector):
        """ Helper method to check the index of data item in list
        :param data: data to match
        :param selector: QComboBox instance
        :return: -1 if not found, index if found
        """
        for i in range(0, selector.count()):
            if selector.itemData(i) == data:
                return i
        return -1

    @staticmethod
    def find_table_item(data, selector):
        """ Helper method to check the index of data item in table
        :param data: data to match
        :param selector: QComboBox instance
        :return: None if not found, item itself if it is found
        """
        model = selector.model()
        for i in range(0, model.columnCount()):
            for j in range(0, model.rowCount()):
                item = model.item(j, i)
                if item and item.data() == data:
                    return item
        return None


    @staticmethod
    def remove_list_item(data, selector):
        """ Helper method to remove items from combo boxes
        :param data: list item's data has to match this
        :param selector: QComboBox instance
        """
        found = False
        for i in range(0, selector.count()):
            if selector.itemData(i) == data:
                found = True
                break
        if found:
            selector.removeItem(i)
            return i
        else:
            return -1


    def selected_objects_changed(self):
        """ Called after ctrl.selection has changed. Prepare panel to use selection as scope
        :return:
        """
        selection = ctrl.get_all_selected()
        found = False
        for item in selection:
            if isinstance(item, Edge):
                found = True
                break
        if found:
            if self.scope != g.SELECTION:
                self._old_scope = self.scope
            self.scope = g.SELECTION
        elif self.scope == g.SELECTION:
            self.scope = self._old_scope


    def change_scope(self, value):
        """ Change the scope of other manipulations in this panel.
        Could change value directly, but just in case.
        :param value: new scope
        :return: None
        """
        self.scope = value

    def update_color(self, color):
        self.current_color = color
        item = self.find_table_item(color, self.color_selector)
        if item:
            self.color_selector.setModelColumn(item.column())


    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has otherwise changed.
        :return:
        """
        self.update_scope_selector_options()
        self.update_scope_selector()
        self.update_fields()

    @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this forest """
        used_scopes = {self.scope}
        for edge in ctrl.main.forest.edges.values():
            used_scopes.add(edge.edge_type)
        scope_list = [x for x in scope_display_order if x in used_scopes]
        self.scope_selector.clear()
        for item in scope_list:
            self.scope_selector.addItem(scope_display_items[item], item)


    def update_scope_selector(self):
        """ Visual update for scope selector value """
        i = self.find_list_item(self.scope, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_fields(self):
        """ Update different fields in the panel to show the correct values based on selection or current scope.
        There may be that this makes fields to remove or add new values to selectors or do other hard manipulation
        to fields.
        """
        def add_and_select_ambiguous_marker(selector):
            i = self.find_list_item(g.AMBIGUOUS_VALUES, selector)
            if i == -1:
                selector.insertItem(0, '---', g.AMBIGUOUS_VALUES)
                selector.setCurrentIndex(0)
            else:
                self.selector.setCurrentIndex(i)

        def add_and_select_ambiguous_marker_to_table(selector):
            item = self.find_table_item(g.AMBIGUOUS_VALUES, selector)
            if item:
                selector.setCurrentIndex(item.row())
                selector.setModelColumn(item.column())
            else:
                row = []
                for i in range(0, selector.model().rowCount()):
                    item = QStandardItem('---')
                    item.setData(g.AMBIGUOUS_VALUES)
                    item.setSizeHint(QSize(22, 20))
                    row.append(item)
                selector.model().insertRow(0, row)
                selector.setCurrentIndex(0)
                selector.setModelColumn(0)


        def remove_ambiguous_marker(selector):
            i = self.find_list_item(g.AMBIGUOUS_VALUES, selector)
            if i > -1:
                selector.removeItem(i)

        def remove_ambiguous_marker_from_table(selector):
            item = self.find_table_item(g.AMBIGUOUS_VALUES, selector)
            if item:
                selector.model().removeRow(item.row())


        ### First find what are the properties of the selected edges.
        ### If they are conflicting, e.g. there are two different colors in selected edges,
        ### then they cannot be shown in the color selector. They can still be overridden with new selection.
        if self.scope == g.SELECTION:
            edge_shape = None
            edge_color = None
            ambiguous_edge = False
            ambiguous_color = False
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    if not edge_shape:
                        edge_shape = edge.shape_name()
                    elif edge.shape_name() != edge_shape:
                        ambiguous_edge = True
                    if not edge_color:
                        edge_color = edge.color_id()
                    elif edge.color() != edge_color:
                        ambiguous_color = True
            ### Color selector - show
            if edge_color:
                if ambiguous_color:
                    add_and_select_ambiguous_marker_to_table(self.color_selector)
                else:
                    remove_ambiguous_marker_from_table(self.color_selector)
                    item = self.find_table_item(edge_color, self.color_selector)
                    assert(item)
                    self.color_selector.setCurrentIndex(item.row())
                    self.color_selector.setModelColumn(item.column())
                    self.current_color = edge_color

            ### Shape selector - show shape of selected edges, or '---' if they contain more than 1 shape.
            if edge_shape:
                if ambiguous_edge:
                    add_and_select_ambiguous_marker(self.shape_selector)
                else:
                    remove_ambiguous_marker(self.shape_selector)
                    i = self.find_list_item(edge_shape, self.shape_selector)
                    self.shape_selector.setCurrentIndex(i)
                    self.shape_selector.update()


        else:
            ### Color selector
            remove_ambiguous_marker_from_table(self.color_selector)
            self.current_color = ctrl.forest.settings.edge_settings(self.scope, 'color')
            item = self.find_table_item(self.current_color, self.color_selector)
            assert(item)
            self.color_selector.setCurrentIndex(item.row())
            self.color_selector.setModelColumn(item.column())

            ### Edge selector
            remove_ambiguous_marker(self.shape_selector)
            edge_shape = ctrl.forest.settings.edge_settings(self.scope, 'shape_name')
            i = self.find_list_item(edge_shape, self.shape_selector)
            assert(i > -1)
            self.shape_selector.setCurrentIndex(i)
            self.shape_selector.update()




