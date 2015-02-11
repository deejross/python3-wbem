"""
WBEM CLI for Python 2.7+ and 3.3+
------------------------------------
This module contains the functionality to create CIM-XML requests and parse CIM-XML responses. In addition,
HTTP(S) is used to provide the communications portion of WBEM.

License
-------
The MIT License (MIT)

Copyright (c) 2015 Ross Peoples <ross.peoples@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import os
import sys

from gui_qt_mainwindow import Ui_MainWindow
from PySide.QtGui import QApplication, QMainWindow, QMessageBox, QTreeWidgetItem
from wbem.cim import InvalidClass
from wbem.client import WBEMClient

# make sure to get the file's current path, even when compiled
try:
    file_path = os.path.abspath(__file__)
except NameError:
    file_path = os.path.abspath(sys.argv[0])


def parse_uri(uri):
    if not uri or '://' not in uri:
        raise ValueError('Full http(s) URI is required')

    protocol, url = uri.split('://', 1)

    try:
        hostinfo, namespace = url.split('/', 1)
    except ValueError:
        hostinfo = url
        namespace = 'root/cimv2'

    try:
        host, port = hostinfo.split(':', 1)
    except ValueError:
        host = hostinfo
        port = 80

    return dict(
        https=protocol.lower() == 'https',
        default_namespace=namespace.strip('/'),
        hostname=host,
        port=port
    )


def compile_exe():
    """
    Creates a standalone EXE file.
    """
    print('\nRunning compile using distutils and py2exe:\n')
    from distutils.core import setup
    import py2exe  # required for proper inclusion

    dll_excludes = ['w9xpopen.exe']
    sys.argv[1] = 'py2exe'
    setup(
        windows=[file_path],
        options=dict(
            py2exe=dict(
                includes=['PySide.QtCore', 'PySide.QtGui', 'PySide.QtNetwork'],
                excludes=['tkinter', 'Tkinter', '_tkinter', 'Tkconstants', 'tcl', 'doctest', 'pdb', 'inspect', 'email'],
                dll_excludes=dll_excludes,
                bundle_files=1,
                compressed=True
            ),
        ),
        zipfile=None
    )

    sys.exit(0)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.txt_address.setFocus()

        # setup event handlers
        self.ui.btn_execute.clicked.connect(self.btn_execute_clicked)

    def btn_execute_clicked(self):
        try:
            self.execute_query()
        except ValueError as ex:
            QMessageBox.critical(self, 'Execution Error', str(ex))

    def execute_query(self):
        class_or_instance = self.ui.cbo_class_or_instance.currentText()
        if not class_or_instance:
            raise ValueError('Requires class or instance name')

        connect_info = parse_uri(self.ui.txt_address.text())
        connect_info['username'] = self.ui.txt_username.text()
        connect_info['password'] = self.ui.txt_password.text()

        c = WBEMClient(**connect_info)
        operation = self.ui.cbo_operation.currentText()
        if operation == 'GetInstance':
            obj = c.Instance(class_or_instance)
        else:
            obj = c.Class(class_or_instance)

        result = getattr(c, operation)(obj)
        nodes = []
        self.ui.tree_results.clear()
        if result.instances:
            for i in result.instances:
                node = QTreeWidgetItem([str(i)])
                if i.properties:
                    for k, v in sorted(i.properties.items()):
                        node.addChild(QTreeWidgetItem([k, str(v)]))
                nodes.append(node)
        elif result.properties:
            node = QTreeWidgetItem(['Properties'])
            for k, v in sorted(result.properties.items()):
                node.addChild(QTreeWidgetItem([k, str(v)]))
            nodes.append(node)
        else:
            nodes.append(QTreeWidgetItem(['No results']))

        self.ui.tree_results.addTopLevelItems(nodes)
        self.ui.tree_results.resizeColumnToContents(0)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '-c':
        compile_exe()

    app = QApplication(sys.argv)
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
