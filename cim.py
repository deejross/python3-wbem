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


import six

# choose the fastest XML implementation available
try:
    # attempt to use LXML, if available
    import lxml.etree as ET
except ImportError:
    try:
        # if no LXML, try to use cElementTree for Python 2.x (deprecated in Python 3.3)
        from xml.etree import cElementTree as ET
    except ImportError:
        # if no cElementTree (not running in CPython or removed in Python 3.5+)
        from xml.etree import ElementTree as ET

import datetime


class CimError(Exception):
    """
    Generic CIM error (code 1 and any other that does not subclass CimError)
    """
    code = 1


class InvalidNamespace(CimError):
    code = 3


class InvalidParameter(CimError):
    code = 4


class InvalidClass(CimError):
    code = 5


class NotFound(CimError):
    code = 6


class NotSupported(CimError):
    code = 7


class InvalidProperty(CimError):
    code = 12


class TypeMismatch(CimError):
    code = 13


class InvalidQuery(CimError):
    code = 15


class InvalidMethod(CimError):
    code = 17


class Class(object):
    """
    Represents a CIM class.
    """
    def __init__(self, name, namespace=None):
        shortcuts_reversed = Instance.shortcuts_reversed()
        if name in shortcuts_reversed:
            name = shortcuts_reversed[name]

        self.name = name
        self.namespace = namespace

    def __str__(self):
        """
        Returns the name of the class
        """
        return self.name

    def __repr__(self):
        """
        Returns a string representation of the class
        """
        return '<wbem.cim.Class: %s in namespace %s>' % (self.name, self.namespace)


class Instance(object):
    """
    Represents a CIM instance. The classname can be shortened for tostring() and fromstring() by adding
    entries to the Instance.shortcuts dictionary on startup. Entries should be in the format:
        original_version=short_version
    Example:
        Instance.shortcuts['DiskStorageSystemWithDisksAndPartitions'] = 'DSSWDAP'
        instance = Instance('DSSWDAP')
        instance.tostring()  # classname=DSSWDAP;namespace=root/cimv2
        instance.toxml()     # <INSTANCENAME CLASSNAME="DiskStorageSystemWithDisksAndPartitions"/>

    Keybindings are stored in a dictionary in one of two forms:
        1) name=value
        2) name=(value, valuetype)
    Keybindings stored with #1 are auto-detected on toxml().
    """

    default_namespace = 'root/cimv2'
    shortcuts = dict()

    def __init__(self, classname, keybindings=None, namespace=None):
        """
        Initializer
        :param classname: The class name of the instance
        :param keybindings: Dictionary of keybindings
        :param namespace: The namespace

        :return:
        """
        shortcuts_reversed = self.shortcuts_reversed()
        if classname in shortcuts_reversed:
            classname = shortcuts_reversed[classname]

        self.classname = classname
        self.keybindings = keybindings or dict()
        self.namespace = namespace

    @classmethod
    def shortcuts_reversed(cls):
        d = dict()
        for k, v in cls.shortcuts.items():
            d[v] = k

        return d

    @staticmethod
    def fromstring(instance):
        """
        Parse an instance string and return an Instance object
        :param instance: String to parse
        :return: Instance
        """
        classname = None
        keybindings = dict()
        namespace = None

        options = instance.strip().split(';')
        for o in options:
            if '=' not in o:
                continue
            key, val = o.split('=', 1)
            if key == '$cn' or key == 'classname':
                classname = val
            elif key == '$ns' or key == 'namespace':
                namespace = val
            else:
                if '?' in val:
                    keybindings[key] = val.split('?', 1)
                else:
                    keybindings[key] = val

        if not classname:
            raise ValueError('The classname option was not found in the instance string')

        return Instance(classname, keybindings, namespace)

    def tostring(self):
        """
        Format the Instance to a string
        :return: string
        """
        classname = self.shortcuts[self.classname] if self.classname in self.shortcuts else self.classname
        output = ['$cn=%s' % classname]
        if self.namespace and self.namespace != self.default_namespace:
            output.append('$ns=%s' % self.namespace)

        for key, val in self.keybindings.items():
            if isinstance(val, (list, tuple)):
                if val[1] != 'string':
                    output.append('%s=%s?%s' % (key, val[0], val[1]))
                else:
                    output.append('%s=%s' % (key, val[0]))
            else:
                output.append('%s=%s' % (key, val))

        return ';'.join(output)

    def toxml(self):
        """
        Format the Instance to XML elements
        :return: Element
        """
        children = []
        for name, val in self.keybindings.items():
            if isinstance(val, (list, tuple)):
                if len(val) != 2:
                    raise ValueError('Encountered sequence with invalid number of items while creating keybindings')
                children.append(Tags.keybinding(name, val[0], val[1]))
            else:
                children.append(Tags.keybinding(name, val))

        return Tags.instancename(children, self.classname)

    def append(self, name, value, valuetype=None):
        """
        Append a keybinding. If valuetype is not given, it will be auto-detected
        :param name: The name
        :param value: The value
        :param valuetype: CIM type
        :return:
        """
        if valuetype:
            v = (value, valuetype)
        else:
            v = value
        self.keybindings[name] = v

    def __str__(self):
        """
        Creates a string version of Instance. This calls tostring()
        :return: string
        """
        return self.tostring()

    def __repr__(self):
        """
        Create a string representation of Instance. This calls tostring()
        :return: string
        """
        return '<wbem.cim.Instance: %s>' % self.tostring()


class Tags(object):
    """
    CIM-XML tag generator
    """

    @staticmethod
    def append_children(parent, children):
        """
        Appends child Elements to the parent Element, returning the parent element for convenience
        :param parent: Parent Element
        :param children: Child Element(s)
        :return: Parent Element
        """
        if children is None or len(children) == 0:
            return parent

        if not isinstance(children, (list, tuple)):
            children = [children]

        parent.extend(children)
        return parent

    @staticmethod
    def cim(children=None, cim_version='2.0', dtd_version='2.0'):
        """
        Root CIM element
        :param children: Child nodes to append
        :param cim_version: CIM Version
        :param dtd_version: DTD Version
        :return: Element

        >>> ET.tostring(Tags.cim())
        <CIM CIMVERSION="x.x" DTDVERSION="x.x"/>
        """
        return Tags.append_children(
            ET.Element('CIM', dict(CIMVERSION=cim_version, DTDVERSION=dtd_version)),
            children
        )

    @staticmethod
    def message(children=None, message_id='1001', protocol_version='1.0'):
        """
        MESSAGE element
        :param children: Child nodes to append
        :param message_id: Message ID
        :param protocol_version: Protocol version
        :return: Element

        >>> ET.tostring(Tags.message())
        <MESSAGE ID="1001" PROTOCOLVERSION="1.0"/>
        """
        return Tags.append_children(
            ET.Element('MESSAGE', dict(ID=message_id, PROTOCOLVERSION=protocol_version)),
            children
        )

    @staticmethod
    def simplereq(children=None):
        """
        SIMPLEREQ element
        :param children: Child nodes to append
        :return: Element

        >>> ET.tostring(Tags.simplereq())
        <SIMPLEREQ/>
        """
        return Tags.append_children(
            ET.Element('SIMPLEREQ'),
            children
        )

    @staticmethod
    def imethodcall(children=None, name='EnumerateInstanceNames'):
        """
        IMETHODCALL element
        :param children: Child nodes to append
        :param name: Name of the method to call
        :return: Element

        >>> ET.tostring(Tags.imethodcall())
        <IMETHODCALL NAME="EnumerateInstanceNames"/>
        """
        return Tags.append_children(
            ET.Element('IMETHODCALL', dict(NAME=name)),
            children
        )

    @staticmethod
    def localnamespacepath(namespace='root/cimv2'):
        """
        LOCALNAMESPACEPATH element
        :param namespace: The namespace path (ex: root/cimv2)
        :return: Element

        >>> ET.tostring(Tags.localnamespacepath())
        <LOCALNAMESPACEPATH><NAMESPACE NAME="root"/><NAMESPACE NAME="cimv2"/></LOCALNAMESPACEPATH>
        """
        children = []
        names = namespace.split('/')
        for n in names:
            children.append(ET.Element('NAMESPACE', dict(NAME=n)))

        return Tags.append_children(
            ET.Element('LOCALNAMESPACEPATH'),
            children
        )

    @staticmethod
    def iparamvalue(children=None, name='ClassName'):
        """
        IPARAMVALUE element
        :param children: Child nodes to append.
        :param name: Name of the parameter
        :return: Element

        >>> ET.tostring(Tags.iparamvalue())
        <IPARAMVALUE NAME="ClassName"/>
        """
        return Tags.append_children(
            ET.Element('IPARAMVALUE', dict(NAME=name)),
            children
        )

    @staticmethod
    def classname(name):
        """
        CLASSNAME element
        :param name: Name of the class
        :return: Element

        >>> ET.tostring(Tags.classname('OperatingSystem'))
        <CLASSNAME NAME="OperatingSystem"/>
        """
        return ET.Element('CLASSNAME', dict(NAME=name))

    @staticmethod
    def instancename(children=None, classname=None):
        """
        INSTANCENAME element
        :param children: Child nodes to append
        :param classname: Name of the class
        :return: Element

        >>> ET.tostring(Tags.instancename('StorageDevice'))
        <INSTANCENAME CLASSNAME="StorageDevice"/>
        """
        return Tags.append_children(
            ET.Element('INSTANCENAME', dict(CLASSNAME=classname)),
            children
        )

    @staticmethod
    def keybinding(name, value=None, value_type=None):
        """
        KEYBINDING and KEYVALUE elements
        :param name: Name of the keybinding
        :param value: Value inside KEYVALUE
        :param value_type: VALUETYPE for KEYVALUE. Defaults to auto-detect
        :return: Element

        >>> ET.tostring(Tags.keybinding(name='Name', value='The Value'))
        <KEYBINDING NAME="Name"><KEYVALUE VALUETYPE="string">The Value</KEYVALUE></KEYBINDING>
        """
        if value:
            if not value_type:
                value, value_type = Tags.autodetect_valuetype(value)

            keyvalue_element = ET.Element('KEYVALUE', dict(VALUETYPE=value_type))
            keyvalue_element.text = value
            children = [keyvalue_element]
        else:
            children = None

        return Tags.append_children(
            ET.Element('KEYBINDING', dict(NAME=name)),
            children
        )

    @staticmethod
    def autodetect_valuetype(value):
        """
        Autodetects a value for the VALUETYPE attribute of a KEYVALUE element
        :param value: The value to autodetect
        :return: (value, value_type)
        """
        if isinstance(value, six.text_type):
            return value, 'string'
        elif isinstance(value, six.binary_type):
            return value.decode('utf-8'), 'string'
        elif isinstance(value, datetime.datetime):
            utc = datetime.datetime.utcnow()
            local = datetime.datetime.now()
            if local < utc:
                offset = '-%s' % int(float((utc - local).seconds) / 60 + 0.5)
            else:
                offset = '+%s' % int(float((local - utc).seconds) / 60 + 0.5)

            return value.strftime('%Y%m%d%H%M%S.%f')+offset, 'datetime'
        elif isinstance(value, datetime.timedelta):
            hours = value.seconds / 3600
            minutes = (value.seconds - hours * 3600) / 60
            return '%08d%02d%02d%02d.%06d:000' % (
                value.days, hours, minutes,
                value.seconds - hours * 3600 - minutes * 60,
                value.microseconds
            )
        elif isinstance(value, bool):
            return 'TRUE', 'boolean' if value else 'FALSE', 'boolean'
        elif isinstance(value, float):
            # take best guess of value_type
            return str(value), 'real32'
        elif isinstance(value, int):
            # take best guess of value_type
            if value < 0:
                return str(value), 'sint32'
            else:
                return str(value), 'uint32'
        else:
            return ValueError('Cannot detect type %s for value %s' % (str(type(value)), repr(value)))


class Helpers(object):
    """
    Helper functions to automate the building of XML tags
    """

    @staticmethod
    def imethodcall(method, class_or_instance_obj):
        """
        Generates an IMETHODCALL XML tree
        :param method: The name of the method to call
        :param class_or_instance_obj: The Class or Instance object
        :return: XML string
        """
        if not isinstance(class_or_instance_obj, (Class, Instance)):
            raise ValueError('Must pass a Class or Instance object')

        if isinstance(class_or_instance_obj, Class):
            iparamvalue_name = 'ClassName'
            params = [
                Tags.classname(class_or_instance_obj.name)
            ]
        else:
            iparamvalue_name = 'InstanceName'
            params = class_or_instance_obj.toxml()

        return Tags.cim(
            Tags.message(
                Tags.simplereq(
                    Tags.imethodcall(
                        name=method,
                        children=[
                            Tags.localnamespacepath(class_or_instance_obj.namespace),
                            Tags.iparamvalue(
                                name=iparamvalue_name,
                                children=params
                            )
                        ]
                    )
                )
            )
        )


class Methods(object):
    """
    Higher-level operations that use the Helpers class
    """

    @staticmethod
    def GetClass(class_obj):
        """
        Generates the XML required for a GetClass method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('GetClass', class_obj)
        )

    @staticmethod
    def EnumerateClasses(class_obj):
        """
        Generates the XML required for a EnumerateClasses method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('EnumerateClasses', class_obj)
        )

    @staticmethod
    def EnumerateClassNames(class_obj):
        """
        Generates the XML required for a EnumerateClassNames method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('EnumerateClassNames', class_obj)
        )

    @staticmethod
    def GetInstance(instance_obj):
        """
        Generates the XML required for a GetInstance method call
        :param instance_obj: Instance object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('GetInstance', instance_obj)
        )

    @staticmethod
    def EnumerateInstances(class_obj):
        """
        Generates the XML required for an EnumerateInstances method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('EnumerateInstances', class_obj)
        )

    @staticmethod
    def EnumerateInstanceNames(class_obj):
        """
        Generates the XML required for an EnumerateInstanceNames method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('EnumerateInstanceNames', class_obj)
        )

    @staticmethod
    def GetProperty():
        raise NotImplementedError()

    @staticmethod
    def SetProperty():
        raise NotImplementedError()

    @staticmethod
    def CreateInstance():
        raise NotImplementedError()

    @staticmethod
    def ModifyInstance():
        raise NotImplementedError()

    @staticmethod
    def DeleteInstance():
        raise NotImplementedError()

    @staticmethod
    def CreateClass():
        raise NotImplementedError()

    @staticmethod
    def ModifyClass():
        raise NotImplementedError()

    @staticmethod
    def DeleteClass(class_obj):
        """
        Generates the XML required for a DeleteClass method call
        :param class_obj: Class object
        :return: XML string
        """
        return ET.tostring(
            Helpers.imethodcall('DeleteClass', class_obj)
        )

    @staticmethod
    def Associators():
        raise NotImplementedError()

    @staticmethod
    def AssociatorNames():
        raise NotImplementedError()

    @staticmethod
    def References():
        raise NotImplementedError()

    @staticmethod
    def ReferenceNames():
        raise NotImplementedError()

    @staticmethod
    def ExecQuery():
        raise NotImplementedError()

    @staticmethod
    def GetQualifier():
        raise NotImplementedError()

    @staticmethod
    def SetQualifier():
        raise NotImplementedError()

    @staticmethod
    def DeleteQualifier():
        raise NotImplementedError()

    @staticmethod
    def EnumerateQualifiers():
        raise NotImplementedError()


class Response(object):
    def __init__(self, xml_string, namespace):
        """
        Parses the given XML string and determines the response
        :param xml_string: The XML string
        :param namespace: The namespace
        :return:
        """
        root = ET.fromstring(xml_string)

        # find the IMETHODRESPONSE element
        imethodresponse = root.find('MESSAGE').find('SIMPLERSP').find('IMETHODRESPONSE')

        # save the method name
        self.method = imethodresponse.attrib['NAME']

        # check for errors
        if imethodresponse.find('ERROR') is not None:
            error_e = imethodresponse.find('ERROR')
            error_code = error_e.attrib['CODE']
            description = error_e.attrib['DESCRIPTION']
            if error_code == '3':
                raise InvalidNamespace(description)
            if error_code == '5':
                raise InvalidClass(description)
            if error_code == '6':
                raise NotFound(description)
            if error_code == '7':
                raise NotSupported(description)
            if error_code == '12':
                raise InvalidProperty(description)
            if error_code == '13':
                raise TypeMismatch(description)
            if error_code == '15':
                raise InvalidQuery(description)
            if error_code == '17':
                raise InvalidMethod(description)

            raise CimError(description)

        # find and store instances, if they exist
        self.instances = []
        for i in imethodresponse.find('IRETURNVALUE').findall('INSTANCENAME'):
            instance = Instance(i.attrib['CLASSNAME'], namespace=namespace)
            for kb in i.findall('KEYBINDING'):
                name = kb.attrib['NAME']
                keyvalue_e = kb.find('KEYVALUE')
                valuetype = keyvalue_e.attrib['VALUETYPE']
                value = self.parse_valuetype(keyvalue_e.text.strip(), valuetype)
                instance.append(name, value, valuetype)

            self.instances.append(instance)

        # find and store properties, if they exist
        self.properties = dict()
        props_parent = imethodresponse.find('IRETURNVALUE').find('INSTANCE')
        if props_parent is not None:
            for p in props_parent.findall('PROPERTY'):
                key = p.attrib['NAME']
                valuetype = p.attrib['TYPE']
                value_e = p.find('VALUE')
                if value_e is not None:
                    value = self.parse_valuetype(value_e.text.strip(), valuetype)
                    self.properties[key] = value
                else:
                    value_array_e = p.find('VALUE.ARRAY')
                    if value_array_e:
                        values = []
                        for v in value_array_e.findall('VALUE'):
                            values.append(self.parse_valuetype(v.text.strip(), valuetype))

                        self.properties[key] = values

    @staticmethod
    def parse_valuetype(value, valuetype):
        """
        Parses the value from a string into the desired Python type
        :param value: The value
        :param valuetype: The CIM type
        :return: Parsed value
        """
        if valuetype == 'string':
            return value

        if 'sint' in valuetype or 'uint' in valuetype:
            return int(value)

        if 'real' in valuetype:
            return float(value)

        if valuetype == 'boolean':
            return True if value.upper() == 'TRUE' else False

        if valuetype == 'datetime':
            if '-' in value:
                dt, offset = value.split('-', 1)
                offset = - int(offset)
            elif '+' in value:
                dt, offset = value.split('+', 1)
                offset = int(offset)
            elif value.endswith(':000') and len(value) == 25:
                return datetime.timedelta(
                    days=int(value[0:8]),
                    hours=int(value[8:10]),
                    minutes=int(value[10:12]),
                    seconds=int(value[12:14]),
                    microseconds=int(value[15:21])
                )
            else:
                dt = value, offset = 0

            return datetime.datetime.strptime(dt, '%Y%m%d%H%M%S.%f') + datetime.timedelta(minutes=offset)

    def __str__(self):
        """
        String representation of the Response
        :return: string
        """
        return '%s Response' % self.method

    def __repr__(self):
        """
        String representation of the Response
        :return:
        """
        return '<wbem.cim.Response: %s, instances: %s, properties: %s>' % (
            self.method, len(self.instances), len(self.properties)
        )
