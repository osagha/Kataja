from PyQt5 import QtWidgets

from kataja.singletons import prefs, ctrl
from kataja.ui.panels.UIPanel import UIPanel
#from PyQt5 import QtMultimedia, QtMultimediaWidgets

__author__ = 'purma'


def change_color_mode(mode):
    """

    :param mode:
    """
    modes = ctrl.cm.ordered_color_modes
    mode_key = list(modes.keys())[mode]
    ctrl.main.change_color_mode(mode_key)


class ColorPanel(UIPanel):
    """
        ⚀	U+2680	&#9856;
        ⚁	U+2681	&#9857;
        ⚂	U+2682	&#9858;
        ⚃	U+2683	&#9859;
        ⚄	U+2684	&#9860;
        ⚅	U+2685	&#9861;
    """

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None,
                 folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        ocm = ctrl.cm.ordered_color_modes
        self.selector_items = [c['name'] for c in ocm.values()]
        selector = QtWidgets.QComboBox(self)
        selector.addItems(self.selector_items)
        selector.activated.connect(change_color_mode)
        self.mode_select = selector
        self.mode_select.setCurrentIndex(list(ocm.keys()).index(ctrl.cm.current_color_mode))

        layout.addWidget(selector)
        # layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()

    def update_colors(self):
        """

        """
        ocm = ctrl.cm.ordered_color_modes
        current_color_modes = [c['name'] for c in ocm.values()]
        if self.selector_items != current_color_modes:
            self.mode_select.clear()
            self.mode_select.addItems(current_color_modes)
        self.mode_select.setCurrentIndex(list(ocm.keys()).index(ctrl.cm.current_color_mode))

