python3-wbem
============
Simplified WBEM client for Python 2.6+ and 3.3+

Motivation
----------
During my conversion of PyWBEM to Python 3, I noticed (in my opinion) a bloat of code. PyWBEM serves many purposes, but my primary motivation for working with WBEM was to read statistics from storage devices. The primary motivation for this library was to create a simple, light, pure-Python WBEM client from scratch using modern syntax with the purpose of gatthering information from WBEM sources.

Current Status
--------------
Fully working read-only functions GetClass, EnumerateClasses, EnumerateClassNames, GetInstance, EnumerateInstances, and EnumerateInstanceNames. These cover most of the needs for pulling information from WBEM devices.

Limitations
-----------
* Only HTTP support, no local socket support yet
* Only read-only methods are being developed currently

Dependencies
------------
There are no required dependencies other than Python 2.6+ or Python 3.3+. However, if lxml is installed, XML will be handled with it. Otherwise, it attempts to import cElementTree (for Python 2.x and non-CPython platforms), and finally choosing regular ElementTree if nothing else is available.

Documentation
-------------
There is no official documentation yet. However, the code base should be small enough to figure out API. Instance and Class objects are returned and given as arguments using WBEMClient. This simplifies the handling of that information, and Instance and Class instances can be serialized to a string, and later deserialized back into objects. This makes CLI tools easier to write that require the user to specify Instances or Classes.

WBEMClient is the primary way to interact with the library. This is its initializer:
* hostname
* port: optional (default: 80)
* username: optional (default: None)
* password: optional (default: None)
* default_namespace: optional (default: root/cimv2)
* debug: optional (default: False)
* https: optional (default: False)

To create Class or Instance objects you can use the client's Class and Instance methods.

For Classes:
```python
client.Class('OperatingSystem')
```

For creating Instance objects using Python code:
```python
client.Instance('OperatingSystem', keybindings=dict(Name='Foo'))
```

For creating Instance objects from serialized strings:
```python
client.Instance('$cn=OperatingSystem;$ns=root/cimv2;Name=Foo')
```

Once you have a Class or Instance object, you can call methods:
* GetClass(class_obj)
* EnumerateClasses(class_obj)
* EnumerateClassNames(class_obj)
* GetInstance(instance_obj)
* EnumerateInstances(class_obj)
* EnumerateInstanceNames(class_obj)

This will return a Response object with the following members:
* method: The method name
* instances: List of Instance objects
* properties: Dictionary of properties found

Example
-------
This is a quick example for listing the instances of a class:
```python
>>> from wbem import WBEMClient
>>> client = WBEMClient('the-host')
>>> client.EnumerateInstanceNames(client.Class('OperatingSystem'))
<wbem.cim.Response: EnumerateInstanceNames, instances: 5, properties: 3>
```

Frontends
-------------
To make testing easier, two GUI frontends and a CLI have been created. Both of the GUIs have nearly identical usage, one uses Tkinter, and the other PySide/Qt. This seemed like a great opportunity to compare GUI frameworks and how well they compile. There also appears to be a lack of free/open-source GUI tools for testing WBEM/CIM providers, which was a secondary motivation for creating the GUIs. The CLI works identically to the GUI frontends, except that information is passed using command-line arguments.

Compiling Binaries
------------------
In the binaries folder, a single executable exists for Windows machines. This was compiled using the PySide/Qt frontend under Python 2.7 with py2exe, as py2exe seems to have several problems under Python 3.4.

For building your own binaries on Windows, you'll need Python 2.7 (x86), py2exe==0.6.9, and PySide==1.1.2 or higher. In addition, you will need to copy msvcp90.dll from C:\Windows\winsxs\x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.21022.8_none_bcb86ed6ac711f91 to C:\Python27\DLLs. If you don't have the exact version number, check the py2exe documentation for getting the Microsoft Visual C 2008 redistributable. Once all of these requirements are satisfied and you are ready to compile, simply run: python gui_qt.py -c

Any changes that need to be made to the Qt GUI can be done with the Qt Designer binary that is installed in the PySide folder in your Python installation's site-packages folder. Any changes made to the py_gui_mainwindow.ui file will require that py_gui_mainwindow.py be regenerated. This can be done by running: pyside-uic gui_qt_mainwindow.ui -o gui_qt_mainwindow.py

Contributions
-------------
As always, I welcome any contributions whether they be code, documentation, tests, bug reports, or feature requests. The WBEM/CIM protocols don't seem to be very popular right now, so any interest in general for WBEM support in Python is appreciated.
