python3-wbem
============
Simplified WBEM client for Python 2.6+ and 3.3+

Motivation
----------
During my conversion of PyWBEM to Python 3, I noticed (in my opinion) a bloat of code. PyWBEM serves many purposes, but my primary motivation for working with WBEM was to read statistics from storage devices. The primary motivation for this library was to create a simple, light, pure-Python WBEM client from scratch using modern syntax with the purpose of gatthering information from WBEM sources.

Current Status
--------------
Under development. The CIM-XML generation required for making read only requests has been completed. Recently, the WBEMClient class was created to handle the communication functions as well as a basic CIM-XML parser, however, it has not been tested yet. Work is underway to get this library in a more stable state.

Limitations
-----------
* No HTTP/SSL support yet
* Only HTTP support, no local socket support yet
* Only read-only methods are being developed currently

Documentation
-------------
Since this library is still under construction, there is no documentation yet. Hopefully, within the next few days it will become more stablized and this section can be filled in with better information.

Contributions
-------------
As always, I welcome any contributions whether they be code, documentation, tests, bug reports, or feature requests. The WBEM/CIM protocols don't seem to be very popular right now, so any interest in general for WBEM support in Python is appreciated.
