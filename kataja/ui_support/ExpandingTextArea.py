from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.utils import open_symbol_data, caller
from kataja.parser.INodes import ITextNode, as_html, as_text, as_editable_latex, as_editable_html
import kataja.globals as g
import html


class MyPlainTextEdit(QtWidgets.QPlainTextEdit):

    def __init__(self, parent, on_focus_out=None):
        super().__init__(parent)
        self.on_focus_out = on_focus_out

    def focusOutEvent(self, event):
        if self.on_focus_out:
            self.on_focus_out()
        super().focusOutEvent(event)

class ExpandingTextArea(QtWidgets.QWidget):

    def __init__(self, parent, tip='', font=None, prefill='', on_edit=None, label=None,
                 on_focus_out=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.raw_text = ''
        self.parsed_latex = ''
        self.parsed_html = ''
        self.parsing_mode = 1
        layout = QtWidgets.QVBoxLayout()
        self.top_row_layout = QtWidgets.QHBoxLayout()
        self.input_parsing_modes = QtWidgets.QButtonGroup()
        self.tex_radio = QtWidgets.QRadioButton("TeX", self)
        self.html_radio = QtWidgets.QRadioButton("HTML", self)
        self.input_parsing_modes.addButton(self.tex_radio, 1)
        self.input_parsing_modes.addButton(self.html_radio, 2)
        self.input_parsing_modes.buttonClicked.connect(self.change_text_field_mode)
        if label:
            lab = QtWidgets.QLabel(label, self)
            self.top_row_layout.addWidget(lab)
            self.top_row_layout.addStretch(0)
        self.top_row_layout.addWidget(self.tex_radio)
        self.top_row_layout.addWidget(self.html_radio)
        self.top_row_layout.addStretch(0)
        layout.addLayout(self.top_row_layout)
        self.text_area = MyPlainTextEdit(parent, on_focus_out)
        self.text_area.setAutoFillBackground(True)
        self.text_area.setSizeAdjustPolicy(self.text_area.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        if not font:
            font = qt_prefs.get_font(g.CONSOLE_FONT)
        self.text_area.setStyleSheet(
            'font-family: "%s"; font-size: %spx; background-color: %s' % (font.family(),
                                                                          font.pointSize(),
                                                                          ctrl.cm.paper().name()))

        self.text_area.setEnabled(True)
        self.cut_point = 24
        self.input_parsing_modes.button(self.get_host().text_parse_mode).setChecked(True)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_area)
        self.setLayout(layout)
        self.text_area.setMinimumHeight(40)
        self.text_area.setMinimumWidth(200)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
        if prefill:
            self.text_area.setPlaceholderText(prefill)
        self.text_area.textChanged.connect(self.text_area_check_for_resize)
        if on_edit:
            self.text_area.textChanged.connect(on_edit)
        self.setAcceptDrops(True)
        self.original_size = None
        self.changed = False

    def get_host(self):
        parent = self.parentWidget()
        if parent:
            return getattr(parent, 'host', None)

    def text(self):
        return self.text_area.toPlainText()

    @caller
    def setText(self, text):
        self.raw_text = text
        print('raw text:', text, type(text))
        self.parsed_latex = as_editable_latex(text)
        print('parsed_latex:', self.parsed_latex)
        self.parsed_html = as_editable_html(text)
        print('parsed_html:', self.parsed_html)
        if self.parsing_mode == 1:
            self.text_area.setPlainText(self.parsed_latex)
        elif self.parsing_mode == 2:
            self.text_area.setPlainText(self.parsed_html)
        #self.text_area.setAlignment(QtCore.Qt.AlignCenter)

    def setFocus(self, *args):
        self.text_area.setFocus(*args)

    def reset(self):
        self.text_area.setPlainText('')
        self.toggle_line_mode()
        if self.original_size:
            self.setFixedSize(self.original_size)
        self.parentWidget().update_size()

    def text_area_check_for_resize(self):
        text = self.text_area.toPlainText()
        if self.parsing_mode == 1:
            if not self.changed and text != self.parsed_latex:
                self.changed = True
        elif self.parsing_mode == 2:
            if not self.changed and text != self.parsed_html:
                self.changed = True

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from
        symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.text_area.insertPlainText(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dropEvent(self, event)

    def change_text_field_mode(self, button_clicked):
        """ Recompose displayed text as TeX, HTML or Plain
        :param button_clicked:
        :return:
        """
        value = self.inode_text()
        self.parsing_mode = self.input_parsing_modes.id(button_clicked)  # 1 = TeX,  2 = HTML,
        # 3 = Plain
        self.get_host().text_parse_mode = self.parsing_mode
        self.parsed_html = as_editable_html(value)
        self.parsed_latex = as_editable_latex(value)
        if self.parsing_mode == 1:
            self.text_area.setPlainText(self.parsed_latex)
        elif self.parsing_mode == 2:
            self.text_area.setPlainText(self.parsed_html)

    def inode_text(self):
        """
        :return:
        """

        if self.changed:
            if self.parsing_mode == 1:
                parser = ctrl.latex_field_parser
            elif self.parsing_mode == 2:
                parser = ctrl.html_field_parser
            else:
                raise ValueError
            return parser.process(self.text())
        else:
            return self.raw_text

    def update_visual(self, **kw):
        """
        :param kw:
        """
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])


class PreviewLabel(QtWidgets.QLabel):

    def __init__(self, parent, tip='', font=None):
        QtWidgets.QLabel.__init__(self, parent)
        if font:
            self.setFont(font)
        self.font_height = self.fontMetrics().height()
        self.setAlignment(QtCore.Qt.AlignCenter)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
