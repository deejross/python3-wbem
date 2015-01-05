"""
WBEM Module for Python 2.6+ and 3.3+
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

import codecs
import socket
import six

from .cim import Class, Instance, Parser

if six.PY2:
    import httplib as http_client
    import urllib as urllib_parse
else:
    import http.client as http_client
    import urllib.parse as urllib_parse


class AuthenticationError(Exception):
    pass


class CimError(Exception):
    pass


class HttpError(Exception):
    pass


class WBEMClient(object):
    def __init__(self, hostname, port=80, username=None, password=None, default_namespace='root/cimv2'):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.default_namespace = default_namespace
        self.max_attempts = 5

    def request(self, xml, headers=None):
        c = http_client.HTTPConnection(self.hostname, port=self.port)

        attempts = 0
        while attempts < self.max_attempts:
            attempts += 1

            c.putrequest('POST', '/cimom')
            c.putheader('Content-type', 'application/xml; charset="utf-8"')
            c.putheader('Content-length', str(len(xml)))

            if self.username and self.password:
                auth = '%s:%s' % (self.username, self.password)
                auth64 = codecs.encode(auth.encode('utf-8'), 'base64').decode('utf-8').replace('\n', '')
                c.putheader('Authorization', 'Basic %s' % auth64)

            if headers:
                for k, v in headers.items():
                    if six.PY2 and isinstance(k, six.text_type):
                        k = k.encode('utf-8')
                    if six.PY2 and isinstance(v, six.text_type):
                        v = v.encode('utf-8')
                    c.putheader(urllib_parse.quote(k), urllib_parse.quote(v))

            try:
                c.endheaders()

                try:
                    c.send(xml)
                except socket.error as ex:
                    if ex[0] != 104 and ex[0] != 32:
                        raise

                response = c.getresponse()
                body = response.read()

                if response.status != 200:
                    if response.status == 401:
                        if attempts >= self.max_attempts:
                            raise AuthenticationError(response.reason)

                    if response.getheader('CIMError', None) and response.getheader('PGErrorDetail'):
                        raise CimError('%s: %s' % (
                            response.getheader('CIMError'),
                            urllib_parse.unquote(response.getheader('PGErrorDetail')))
                        )

                    raise CimError(response.reason)
            except http_client.BadStatusLine as ex:
                raise HttpError('The web server returned a bad status line: %s' % ex)
            except socket.error as ex:
                raise HttpError('Socket error: %s' % ex)

            break

        return body

    def imethodcall(self, method, class_or_instance_obj, xml):
        headers = dict(
            CIMOperation='MethodCall',
            CIMMethod=method
        )

        if isinstance(class_or_instance_obj, Class):
            headers['CIMObject'] = '%s:%s' % (class_or_instance_obj.name, class_or_instance_obj.namespace)
        elif isinstance(class_or_instance_obj, Instance):
            s = '//%s/%s:%s.' % (self.hostname, class_or_instance_obj.namespace, class_or_instance_obj.classname)
            kbs = []
            for k, v in class_or_instance_obj.keybindings.items():
                if not isinstance(v, six.text_type):
                    v = str(v)

                kbs.append('%s=%s' % (k, v))

            headers['CIMObject'] = s + ','.join(kbs)

        response = self.request(xml, headers)
        return Parser(response)