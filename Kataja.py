#! /usr/bin/env python3.4
# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtCore
import os

filePath = os.path.dirname(os.path.abspath(__file__))
print(filePath)
if filePath.endswith('Resources'):
    QtCore.QCoreApplication.setLibraryPaths([filePath + '/../plugins'])
print('librarypath:', QtCore.QCoreApplication.libraryPaths())


from PyQt5 import QtWidgets, QtPrintSupport
from kataja.KatajaMain import KatajaMain
import sys

# QtPrintSupport is imported here only because py2app then knows to add it as a framework.
# libqcocoa.dynlib requires QtPrintSupport.
ok = QtPrintSupport

app = QtWidgets.QApplication(sys.argv)
app.setApplicationName('Kataja')
app.setOrganizationName('JPurma-Aalto')
app.setOrganizationDomain('jpurma.aalto.fi')
app.setStyle('Fusion')
print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))
print(app.applicationFilePath())
window = KatajaMain(app, sys.argv)
window.show()
app.exec_()
