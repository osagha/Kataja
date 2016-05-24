from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui_support.EmbeddedLineEdit import EmbeddedLineEdit
from kataja.ui_support.EmbeddedMultibutton import EmbeddedMultibutton
from kataja.ui_support.EmbeddedRadiobutton import EmbeddedRadiobutton
from kataja.ui_support.ExpandingLineEdit import ExpandingLineEdit
from kataja.ui_support.ResizeHandle import ResizeHandle
from kataja.ui_support.EmbeddedTextarea import EmbeddedTextarea
from kataja.parser.INodes import ITextNode
from kataja.parser.LatexToINode import LatexFieldToINode
from kataja.singletons import prefs, qt_prefs, ctrl
from kataja.ui_items.UIEmbed import UIEmbed
import kataja.globals as g


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None, align=None):
    label = QtWidgets.QLabel(text, parent=parent)
    if palette:
        label.setPalette(palette)
    label.setFont(qt_prefs.font(g.UI_FONT))
    label.setBuddy(buddy)
    label.setStatusTip(tooltip)
    if ctrl.main.use_tooltips:
        label.setToolTip(tooltip)
    if align:
        layout.addWidget(label, 1, align)
    else:
        layout.addWidget(label)
    return label


class NodeEditEmbed(UIEmbed):
    """ Node edit embed creates editable elements based on templates provided by Node subclass.
    It allows easy UI generation for user-customized syntactic elements or Kataja Nodes.

    :param parent: QWidget where this editor lives, QGraphicsView of some sort
    :param ui_manager: UIManager instance that manages this editor
    :param ui_key: unique, but predictable key for accessing this editor
    :param node: node that is to be associated with this editor
    """

    def __init__(self, parent, node):
        nname = node.name[0].lower()
        UIEmbed.__init__(self, parent, node, 'Edit ' + nname)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        ui_p = self._palette
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())
        smaller_font = qt_prefs.font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)

        ed = node.get_editing_template()
        field_names = node.get_editable_field_names()
        self.fields = {}
        self.resize_target = None
        hlayout = None

        # Generate edit elements based on data, expand this as necessary
        for field_name in field_names:
            d = ed.get(field_name, {})
            if d.get('hidden', False) or not self.host.check_conditions(d):
                continue
            tt = d.get('tooltip', '')
            itype = d.get('input_type', 'text')
            prefill = d.get('prefill', '')
            syntactic = d.get('syntactic', False)
            field_first = False
            field = None
            if itype == 'text':
                width = d.get('width', 140)
                field = EmbeddedLineEdit(self, tip=tt, font=big_font, prefill=prefill)
                field.setMaximumWidth(width)
            elif itype == 'textarea':
                self.disable_effect = True
                template_width = d.get('width', 0)
                field = EmbeddedTextarea(self, tip=tt, font=smaller_font, prefill=prefill)
                nc = node.label_object
                max_w = 200
                if nc.user_width:
                    w = nc.user_width
                elif template_width:
                    w = template_width
                else:
                    w = nc.document().idealWidth()
                if w > 200:
                    w = 200
                field.setFixedWidth(w)
                self.resize_target = field
            elif itype == 'expandingtext':
                field = ExpandingLineEdit(self,
                                          tip=tt,
                                          big_font=big_font,
                                          smaller_font=smaller_font,
                                          prefill=prefill)
                #field.setMaximumWidth(width)
            elif itype == 'multibutton':
                # currently not used, radio button is better
                width = d.get('width', 200)
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or getattr(self.syntactic_object,
                                                                       op_func, None)
                field = EmbeddedMultibutton(self, options=op_func())
                field.setMaximumWidth(width)
            elif itype == 'checkbox':
                #width = d.get('width', 200)
                field = QtWidgets.QCheckBox(self)
                #field.setMaximumWidth(width)
            elif itype == 'radiobutton':
                width = d.get('width', 200)
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or \
                          getattr(self.syntactic_object, op_func, None)
                field = EmbeddedRadiobutton(self, options=op_func())
                field.setMaximumWidth(width)
                field_first = False
            else:
                raise NotImplementedError

            if field:
                action = d.get('select_action')
                if action:
                    self.ui_manager.connect_element_to_action(field, action)
                if syntactic:
                    field.setPalette(ui_s)
                else:
                    field.setPalette(ui_p)

            align = d.get('align', 'newline')
            if align == 'newline':
                # new hlayout means new line, but before starting a new hlayout,
                # end the previous one.
                if hlayout:
                    layout.addLayout(hlayout)
                hlayout = QtWidgets.QHBoxLayout()
            self.fields[field_name] = field
            if field_first:
                hlayout.addWidget(field)
            ui_name = d.get('name', field_name)
            if ui_name:
                if syntactic:
                    palette = ui_s
                else:
                    palette = ui_p
                make_label(ui_name, self, hlayout, tt, field, palette)
            if not field_first:
                hlayout.addWidget(field)
        if hlayout:
            layout.addLayout(hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        self.ui_manager.connect_element_to_action(self.enter_button, 'finish_editing_node')
        hlayout.addWidget(self.enter_button)
        if self.resize_target:
            self.resize_handle = ResizeHandle(self, self.resize_target)
            hlayout.addWidget(self.resize_handle, 0, QtCore.Qt.AlignRight)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.update_embed()
        self.update_position()
        self.hide()


    def margin_x(self):
        """ Try to keep all of the host node visible, not covered by this editor.
        :return:
        """
        return (self.host.boundingRect().width() / 2) + 12

    def margin_y(self):
        """ Try to keep all of the host node visible, not covered by this editor.
        :return:
        """
        return self.host.boundingRect().height() / 2

    def update_fields(self):
        """ Update field values on embed form based on template """
        ed = self.host.get_editing_template()
        for field_name, field in self.fields.items():
            d = ed.get(field_name, {})
            if 'getter' in d:
                value = getattr(self.host, d['getter'])()
            else:
                value = getattr(self.host, field_name, '')
            itype = d.get('input_type', 'text')
            if itype in ['text', 'textarea', 'expandingtext']:
                if isinstance(value, ITextNode):
                    parsed = value.as_html()
                else:
                    parsed = value
                field.setText(parsed)
            elif itype == 'checkbox':
                field.setChecked(bool(value))
            elif itype == 'multibutton':
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or getattr(self.syntactic_object,
                                                                       op_func, None)
                field.update_selections(op_func())

    def after_close(self):
        """ Try to remove this embed after closing
        :return:
        """
        self.ui_manager.remove_edit_embed(self)

    def submit_values(self):
        """ Submit field values back to object based on template
        :return:
        """
        ed = self.host.get_editing_template()
        for field_name, field in self.fields.items():
            d = ed.get(field_name, {})
            itype = d.get('input_type', 'text')
            if itype in ['text', 'textarea', 'expandingtext']:
                parser = LatexFieldToINode(field.text())
                value = parser.node
            elif itype in ['multibutton', 'radiobutton', 'checkbox']:
                # buttons take action immediately when clicked
                continue
            else:
                raise NotImplementedError
            if 'setter' in d:
                getattr(self.host, d['setter'])(value)
            else:
                setattr(self.host, field_name, value)
        self.host.update_label()

    def focus_to_main(self):
        """ Find the main element to focus in this embed.
        :return:
        """
        # look for explicit focus in template definitions.
        ed = self.host.get_editing_template()
        for key, data in ed.items():
            if 'focus' in data and data['focus']:
                self.fields[key].setFocus()
                return
        # default to first field in field order
        if self.fields:
            self.fields[self.host.get_editable_field_names()[0]].setFocus()
