from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.SelectionBox import SelectionBox

__author__ = 'purma'


class SyntaxPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.setMinimumHeight(40)
        inner.setMaximumHeight(50)
        inner.preferred_size = QtCore.QSize(220, 40)
        inner.sizeHint = self.sizeHint

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)

        selector = SelectionBox(self)
        self.selector = selector
        for key, item in []:
            selector.addItem('%s (%s)' % (key, item.shortcut), key)

        self.ui_manager.connect_element_to_action(selector, 'set_visualization')
        hlayout.addWidget(selector)
        self.toggle_options = PanelButton(pixmap=qt_prefs.settings_pixmap,
                                          tooltip='Visualization settings',
                                          parent=self, size=20)
        self.toggle_options.setFixedSize(26, 26)
        self.toggle_options.setCheckable(True)
        ctrl.ui.connect_element_to_action(self.toggle_options, 'toggle_panel_%s' % g.VIS_OPTIONS)
        hlayout.addWidget(self.toggle_options, 1, QtCore.Qt.AlignRight)

        layout.addLayout(hlayout)
        inner.setLayout(layout)
        self.watchlist = ['forest_changed']
        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

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
        if signal == 'forest_changed':
            keeper = ctrl.main.forest_keeper
            if keeper is not None:
                display_index = keeper.current_index + 1
                max_index = len(keeper.forests)
                self.treeset_counter.setText('%s/%s' % (display_index, max_index))
