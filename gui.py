"""
WBEM GUI for Python 2.7+ and 3.3+
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
import sys
if sys.version[0] == '2':
    from Tkinter import *
    import tkMessageBox as messagebox
    import ttk
else:
    from tkinter import *
    from tkinter import messagebox
    from tkinter import ttk


# hack to make script work in same directory as package
try:
    from .cim import InvalidClass
    from .client import WBEMClient
except (ImportError, SystemError, ValueError):
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from wbem import WBEMClient
    from wbem.cim import InvalidClass


class MainApplication(ttk.Frame, object):
    @staticmethod
    def _pad_widgets(frame, padx=5, pady=5):
        for c in frame.winfo_children():
            if c.widgetName.endswith('label'):
                continue
            c.grid_configure(padx=padx, pady=pady)

    @staticmethod
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

    def __init__(self, parent, *args, **kwargs):
        super(MainApplication, self).__init__(parent, *args, **kwargs)

        # set some global options
        parent.title('WBEM GUI')
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        # grid self
        self.grid(column=0, row=0, sticky=(N, S, E, W))

        # initialize container frames
        self._initialize_connect_frame()
        self._initialize_operations_frame()
        self._initialize_results_frame()

        # configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    def _initialize_connect_frame(self, row=0):
        # initialize widgets
        self.frm_connect = ttk.Frame(self)
        self.txt_uri = ttk.Entry(self.frm_connect)
        self.txt_username = ttk.Entry(self.frm_connect)
        self.txt_password = ttk.Entry(self.frm_connect, show='*')

        # grid widgets and labels
        self.frm_connect.grid(column=0, row=row, sticky=(N, S, E, W))
        ttk.Label(self.frm_connect, text='URI').grid(column=0, row=0, sticky=W)
        ttk.Label(self.frm_connect, text='Username').grid(column=1, row=0, sticky=W)
        ttk.Label(self.frm_connect, text='Password').grid(column=2, row=0, sticky=W)
        self.txt_uri.grid(column=0, row=1, sticky=(E, W))
        self.txt_username.grid(column=1, row=1, sticky=(E, W))
        self.txt_password.grid(column=2, row=1, sticky=(E, W))

        # configure grid
        self.frm_connect.columnconfigure(0, weight=3)
        self.frm_connect.columnconfigure(1, weight=1)
        self.frm_connect.columnconfigure(2, weight=1)
        self._pad_widgets(self.frm_connect)

    def _initialize_operations_frame(self, row=1):
        # initialize widgets
        self.frm_operations = ttk.Frame(self)
        self.val_operation = StringVar(value='EnumerateInstances')
        self.cbo_operation = ttk.Combobox(
            self.frm_operations, state='readonly', textvariable=self.val_operation,
            values=('EnumerateInstances', 'EnumerateInstanceNames', 'GetInstance')
        )
        self.txt_class_or_instance = ttk.Entry(self.frm_operations)
        self.btn_execute = ttk.Button(self.frm_operations, text='Execute', command=self.btn_execute_evt)

        # grid widgets
        self.frm_operations.grid(column=0, row=row, sticky=(N, S, E, W))
        ttk.Label(self.frm_operations, text='Operation').grid(column=0, row=0, sticky=W)
        ttk.Label(self.frm_operations, text='Class or instance').grid(column=0, row=2, sticky=W)
        self.cbo_operation.grid(column=0, row=1, sticky=W)
        self.txt_class_or_instance.grid(column=0, row=3, sticky=(E, W))
        self.btn_execute.grid(column=0, row=4, sticky=E)

        # configure grid
        self.frm_operations.columnconfigure(0, weight=1)
        self._pad_widgets(self.frm_operations)

    def _initialize_results_frame(self, row=2):
        # initialize widgets
        self.frm_results = ttk.Frame(self)
        self.txt_results = Text(self.frm_results)
        self.txt_results.insert(END, 'Waiting for execution...')

        # grid widgets
        self.frm_results.grid(column=0, row=row, sticky=(N, S, E, W))
        self.txt_results.grid(column=0, row=0, sticky=(N, S, E, W))

        # configure grid
        self.frm_results.columnconfigure(0, weight=1)
        self.frm_results.rowconfigure(0, weight=1)
        self._pad_widgets(self.frm_results)

    def btn_execute_evt(self, *args):
        try:
            self.execute_query()
        except ValueError as ex:
            messagebox.showerror(message=str(ex))
            raise

    def execute_query(self):
        class_or_instance = self.txt_class_or_instance.get()
        if not class_or_instance:
            raise ValueError('Requires class or instance name')

        connect_info = self.parse_uri(self.txt_uri.get())
        connect_info['username'] = self.txt_username.get() or None
        connect_info['password'] = self.txt_password.get() or None
        connect_info['debug'] = True

        c = WBEMClient(**connect_info)
        operation = self.cbo_operation.get()
        if operation == 'GetInstance':
            obj = c.Instance(class_or_instance)
        else:
            obj = c.Class(class_or_instance)

        try:
            result = getattr(c, operation)(obj)
        except InvalidClass as ex:
            raise ValueError(str(ex))

        self.txt_results.delete('1.0', END)
        if result.instances:
            self.txt_results.insert(END, 'Instance names:\n')
            for i in result.instances:
                self.txt_results.insert(END, str(i) + '\n')
        elif result.properties:
            self.txt_results.insert(END, 'Properties:\n')
            for k, v in result.properties:
                self.txt_results.insert(END, '%s: %s\n' % (k, v))
        else:
            self.txt_results.insert(END, 'No results')


if __name__ == '__main__':
    root = Tk()
    MainApplication(root)
    root.mainloop()
