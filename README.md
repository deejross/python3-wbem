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
* No HTTPS/SSL/TLS support yet
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

Contributions
-------------
As always, I welcome any contributions whether they be code, documentation, tests, bug reports, or feature requests. The WBEM/CIM protocols don't seem to be very popular right now, so any interest in general for WBEM support in Python is appreciated.
