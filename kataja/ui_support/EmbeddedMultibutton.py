from PyQt5 import QtWidgets

from kataja.singletons import ctrl


class EmbeddedMultibutton(QtWidgets.QFrame):
    """

    :param parent:
    :param tip:
    :param options:
    """

    def __init__(self, parent, options=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setAutoFillBackground(False)
        self.bgroup = QtWidgets.QButtonGroup(self)
        self.bgroup.setExclusive(False)
        self.layout = QtWidgets.QHBoxLayout()
        self.update_selections(options)
        self.setLayout(self.layout)

    def update_selections(self, options):
        """ Redraw all buttons
        :param options: iterable of (text, value, is_checked, disabled,
        tooltip) -dictionaries
        :return:
        """
        new_values = set([od['value'] for od in options])
        old_values = set([button.my_value for button in self.bgroup.buttons()])

        # clear old buttons
        for button in self.bgroup.buttons():
            if button.my_value not in new_values:
                self.bgroup.removeButton(button)
                self.layout.removeWidget(button)
                button.destroy()
            else:  # update old button
                for od in options:
                    if od['value'] == button.my_value:
                        button.setChecked(od['is_checked'])
                        if ctrl.main.use_tooltips:
                            button.setToolTip(od['tooltip'])
                            button.setToolTipDuration(2000)
                        button.setStatusTip(od['tooltip'])

                        button.setEnabled(od['enabled'])
                        break
        # create new buttons
        for od in options:
            v = od['value']
            if v not in old_values:
                button = QtWidgets.QPushButton(od['text'])
                button.setStyleSheet(':checked {border-width: 2px;}')
                button.setCheckable(True)
                button.my_value = v
                button.setChecked(od['is_checked'])
                if ctrl.main.use_tooltips:
                    button.setToolTip(od['tooltip'])
                    button.setToolTipDuration(2000)
                button.setStatusTip(od['tooltip'])
                button.setEnabled(od['enabled'])
                self.bgroup.addButton(button)
                self.layout.addWidget(button)
