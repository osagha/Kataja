# coding=utf-8
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.OverlayButton import TopRowButton
from kataja.ui_widgets.ModeLabel import ModeLabel


class TopBarButtons(QtWidgets.QFrame):

    def __init__(self, parent, ui):
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()
        self._left_buttons = []
        self._right_buttons = []

        # Left side
        self.edit_mode_button = ModeLabel(['Free drawing mode', 'Derivation mode'],
                                          ui_key='edit_mode_label',
                                          parent=self)
        layout.addWidget(self.edit_mode_button)
        ui.add_ui(self.edit_mode_button)
        self._left_buttons.append(self.edit_mode_button)
        ui.connect_element_to_action(self.edit_mode_button, 'switch_edit_mode')

        layout.addStretch(0)

        # Right side
        self.view_mode_button = ModeLabel(['Show all objects', 'Show only syntactic objects'],
                                          ui_key='view_mode_label',
                                          parent=self)
        layout.addWidget(self.view_mode_button)
        ui.add_ui(self.view_mode_button)
        self._right_buttons.append(self.view_mode_button)
        ui.connect_element_to_action(self.view_mode_button, 'switch_view_mode')

        camera = TopRowButton('print_button', parent=self, tooltip='Print to file',
                              pixmap=qt_prefs.camera_icon, size=(24, 24))
        ui.add_button(camera, action='print_pdf')
        self._right_buttons.append(camera)
        layout.addWidget(camera)

        undo = TopRowButton('undo_button', parent=self, tooltip='Undo last action',
                            pixmap=qt_prefs.undo_icon)
        ui.add_button(undo, action='undo')
        self._right_buttons.append(undo)
        layout.addWidget(undo)

        redo = TopRowButton('redo_button', parent=self, tooltip='Redo action',
                            pixmap=qt_prefs.redo_icon)
        ui.add_button(redo, action='redo')
        self._right_buttons.append(redo)
        layout.addWidget(redo)

        pan_mode = TopRowButton('pan_mode', parent=self, tooltip='Move mode', size=(24, 24),
                                pixmap=qt_prefs.pan_icon)  # draw_method=drawn_icons.pan_around
        ui.add_button(pan_mode, action='toggle_pan_mode')
        pan_mode.setCheckable(True)
        layout.addWidget(pan_mode)
        self._right_buttons.append(pan_mode)

        select_mode = TopRowButton('select_mode', parent=self, tooltip='Move mode',
                                   pixmap=qt_prefs.select_all_icon,
                                   size=(24, 24))  # draw_method=drawn_icons.select_mode
        select_mode.setCheckable(True)
        ui.add_button(select_mode, action='toggle_select_mode')
        layout.addWidget(select_mode)

        self._right_buttons.append(select_mode)

        fit_to_screen = TopRowButton('fit_to_screen', parent=self,
                                     tooltip='Fit to screen', size=(24, 24),
                                     pixmap=qt_prefs.full_icon)
        # draw_method=drawn_icons.fit_to_screen)
        ui.add_button(fit_to_screen, action='zoom_to_fit')
        layout.addWidget(fit_to_screen)
        self._right_buttons.append(fit_to_screen)

        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(28)
        min_width = 0
        for item in self._left_buttons + self._right_buttons:
            min_width += item.width()
            min_width += 4
        min_width += 10
        self.update_position()

    def sizeHint(self):
        return QtCore.QSize(self.parentWidget().width()-4, 28)

    def update_position(self):
        """ Make sure that float buttons are on graph view's top right corner
        :return:
        """
        self.resize(self.sizeHint())
        self.move(4, 2)
        self.show()

    def left_edge_of_right_buttons(self):
        return self._right_buttons[0].x()