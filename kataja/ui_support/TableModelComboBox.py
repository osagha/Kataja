from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QSize

import kataja.globals as g


class TableModelComboBox(QtWidgets.QComboBox):
    """

    :param args:
    :param kwargs:
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def find_item(self, data):
        """ Return the item corresponding to this data
        :param data: data to match
        :return: None if not found, item itself if it is found
        """
        model = self.model()
        for i in range(0, model.columnCount()):
            for j in range(0, model.rowCount()):
                item = model.item(j, i)
                if item and item.data() == data:
                    return item
        return None


    def select_data(self, data):
        """

        :param data:
        :raise hell:
        """
        item = self.find_item(data)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())
        else:
            print("couldn't find data %s from selector model" % data)
            raise hell

    def currentData(self,  **kwargs):
        """

        :param kwargs:
        :return:
        """
        i = self.view().currentIndex()
        item = self.model().itemFromIndex(i)
        if item:
            return item.data()
        else:
            return None