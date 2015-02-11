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
import argparse
import codecs
import os
import sys

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

    typelibs = []
    com_server = []
    dll_excludes = ['w9xpopen.exe']
    sys.argv[1] = 'py2exe'
    setup(
        console=[file_path],
        com_server=com_server,
        options=dict(
            py2exe=dict(
                typelibs=typelibs,
                includes=[],
                excludes=['tkinter', 'Tkinter', '_tkinter', 'Tkconstants', 'tcl', 'doctest', 'pdb', 'inspect', 'email'],
                dll_excludes=dll_excludes,
                bundle_files=1,
                compressed=True
            ),
        ),
        zipfile=None
    )

    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username')
    parser.add_argument('--password')
    parser.add_argument('--pass64', help='The base64 encoded password, replaces the --password option')
    parser.add_argument('--address', help='The URL to the device, including namespace', required=True)
    parser.add_argument('--method', help='The name of the method to call (EnumerateInstances, GetInstance, etc)', required=True)
    parser.add_argument('--name', help='The class name (i.e. CIM_ComputerSystem) or the instance name', required=True)
    if '__file__' in globals() and sys.platform == 'win32':
        parser.add_argument('-c', help='Compile to EXE with py2exe', dest='compile')

    argv = parser.parse_args()
    if argv.compile:
        compile_exe()

    if argv.pass64:
        password = codecs.decode(codecs.encode(argv.pass64, 'utf-8'), 'base64').decode('utf-8')
    else:
        password = argv.password

    try:
        connect_info = parse_uri(argv.address)
        connect_info['username'] = argv.username
        connect_info['password'] = password

        c = WBEMClient(**connect_info)
    except ValueError as ex:
        print(ex)
        sys.exit(1)

    if not hasattr(c, argv.method):
        print('%s is not a valid method' % argv.method)
        sys.exit(2)

    if argv.method == 'GetInstance':
        obj = c.Instance(argv.name)
    else:
        obj = c.Class(argv.name)

    try:
        result = getattr(c, argv.method)(obj)
    except InvalidClass as ex:
        print(ex)
        sys.exit(3)

    if result.instances:
        print('Instance names:')
        for i in result.instances:
            print('  %s' % i)
            if i.properties:
                print('  Properties:')
                for k, v in sorted(i.properties.items()):
                    print('    %s: %s' % (k, v))
    elif result.properties:
        print('Properties')
        for k, v in sorted(result.properties.items()):
            print('  %s: %s' % (k, v))
    else:
        print('No results')