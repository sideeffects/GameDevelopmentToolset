"""Implements base class for bitstruct types."""

# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, Python File Format Interface
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the Python File Format Interface
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****
# --------------------------------------------------------------------------

# note: some imports are defined at the end to avoid problems with circularity

from functools import partial
from itertools import izip
import struct

from pyffi.object_models.editable import EditableSpinBox # for Bits
from pyffi.utils.graph import DetailNode, EdgeFilter

class _MetaBitStructBase(type):
    """This metaclass checks for the presence of a _attrs attribute.
    For each attribute in _attrs, an <attrname> property is generated which
    gets and sets bit fields. Used as metaclass of BitStructBase."""
    def __init__(cls, name, bases, dct):
        super(_MetaBitStructBase, cls).__init__(name, bases, dct)
        # consistency checks
        if not '_attrs' in dct:
            raise TypeError('%s: missing _attrs attribute'%cls)
        if not '_numbytes' in dct:
            raise TypeError('%s: missing _numbytes attribute'%cls)

        # check storage type
        if cls._numbytes == 1:
            cls._struct = 'B'
        elif cls._numbytes == 2:
            cls._struct = 'H'
        elif cls._numbytes == 4:
            cls._struct = 'I'
        else:
            raise RuntimeError("unsupported bitstruct numbytes")

        # template type?
        cls._is_template = False
        # does the type contain a Ref or a Ptr?
        cls._has_links = False
        # does the type contain a Ref?
        cls._has_refs = False
        # does the type contain a string?
        cls._has_strings = False
        for attr in dct['_attrs']:
            # get and set basic attributes
            setattr(cls, attr.name, property(
                partial(BitStructBase.get_attribute, name = attr.name),
                partial(BitStructBase.set_attribute, name = attr.name),
                doc=attr.doc))

        # precalculate the attribute list
        cls._attribute_list = cls._get_attribute_list()

        # precalculate the attribute name list
        cls._names = cls._get_names()

class Bits(DetailNode, EditableSpinBox):
    """Basic implementation of a n-bit unsigned integer type (without read
    and write)."""
    def __init__(self, numbits = 1, default = 0, parent = None):
        # parent disabled for performance
        #self._parent = weakref.ref(parent) if parent else None
        self._value = default
        self._numbits = numbits

    def get_value(self):
        """Return stored value."""
        return self._value

    def set_value(self, value):
        """Set value to C{value}."""
        if not isinstance(value, (int, long)):
            raise TypeError("bitstruct attribute must be integer")
        if value >> self._numbits:
            raise ValueError('value out of range (%i)' % value)
        self._value = value

    def __str__(self):
        return str(self.get_value())

    # DetailNode

    def get_detail_display(self):
        """Return an object that can be used to display the instance."""
        return str(self._value)

    # EditableSpinBox functions

    def get_editor_value(self):
        return self.get_value()

    def set_editor_value(self, editorvalue):
        self.set_value(editorvalue)

    def get_editor_minimum(self):
        return 0

    def get_editor_maximum(self):
        return (1 << self._numbits) - 1

class BitStructBase(DetailNode):
    """Base class from which all file bitstruct types are derived.

    The BitStructBase class implements the basic bitstruct interface:
    it will initialize all attributes using the class interface
    using the _attrs class variable, represent them as strings, and so on.
    The class variable _attrs must be declared every derived class
    interface.

    Each item in the class _attrs list stores the information about
    the attribute as stored for instance in the xml file, and the
    _<name>_value_ instance variable stores the actual attribute
    instance.

    Direct access to the attributes is implemented using a <name>
    property which invokes the get_attribute and set_attribute
    functions, as demonstrated below.

    See the pyffi.XmlHandler class for a more advanced example.

    >>> from pyffi.object_models.xml.basic import BasicBase
    >>> from pyffi.object_models.xml.expression import Expression
    >>> from pyffi.object_models.xml import BitStructAttribute as Attr
    >>> class SimpleFormat(object):
    ...     @staticmethod
    ...     def name_attribute(name):
    ...         return name
    >>> class Flags(BitStructBase):
    ...     _numbytes = 1
    ...     _attrs = [
    ...         Attr(SimpleFormat, dict(name = 'a', numbits = '3')),
    ...         Attr(SimpleFormat, dict(name = 'b', numbits = '1'))]
    >>> SimpleFormat.Flags = Flags
    >>> y = Flags()
    >>> y.a = 5
    >>> y.b = 1
    >>> print(y) # doctest:+ELLIPSIS
    <class 'pyffi.object_models.xml.bit_struct.Flags'> instance at 0x...
    * a : 5
    * b : 1
    <BLANKLINE>
    >>> y.to_int(None)
    13
    >>> y.from_int(9, None)
    >>> print(y) # doctest:+ELLIPSIS
    <class 'pyffi.object_models.xml.bit_struct.Flags'> instance at 0x...
    * a : 1
    * b : 1
    <BLANKLINE>
    """

    __metaclass__ = _MetaBitStructBase

    _attrs = []
    _numbytes = 1 # default width of a bitstruct
    _games = {}
    arg = None # default argument

    # initialize all attributes
    def __init__(self, template = None, argument = None, parent = None):
        """The constructor takes a tempate: any attribute whose type,
        or template type, is type(None) - which corresponds to
        TEMPLATE in the xml description - will be replaced by this
        type. The argument is what the ARG xml tags will be replaced with.

        :param template: If the class takes a template type
            argument, then this argument describes the template type.
        :param argument: If the class takes a type argument, then
            it is described here.
        :param parent: The parent of this instance, that is, the instance this
            array is an attribute of."""
        # used to track names of attributes that have already been added
        # is faster than self.__dict__.has_key(...)
        names = []
        # initialize argument
        self.arg = argument
        # save parent (note: disabled for performance)
        #self._parent = weakref.ref(parent) if parent else None
        # initialize item list
        # this list is used for instance by qskope to display the structure
        # in a tree view
        self._items = []
        # initialize attributes
        for attr in self._attribute_list:
            # skip attributes with dupiclate names
            if attr.name in names:
                continue
            names.append(attr.name)

            # instantiate the integer
            if attr.default != None:
                attr_instance = Bits(numbits = attr.numbits,
                                     default = attr.default,
                                     parent = self)
            else:
                attr_instance = Bits(numbits = attr.numbits,
                                     parent = self)

            # assign attribute value
            setattr(self, "_%s_value_" % attr.name, attr_instance)

            # add instance to item list
            self._items.append(attr_instance)

    def deepcopy(self, block):
        """Copy attributes from a given block (one block class must be a
        subclass of the other). Returns self."""
        # check class lineage
        if isinstance(self, block.__class__):
            attrlist = block._get_filtered_attribute_list()
        elif isinstance(block, self.__class__):
            attrlist = self._get_filtered_attribute_list()
        else:
            raise ValueError("deepcopy: classes %s and %s unrelated"
                             % (self.__class__.__name__, block.__class__.__name__))
        # copy the attributes
        for attr in attrlist:
            setattr(self, attr.name, getattr(block, attr.name))

        return self

    # string of all attributes
    def __str__(self):
        text = '%s instance at 0x%08X\n' % (self.__class__, id(self))
        # used to track names of attributes that have already been added
        # is faster than self.__dict__.has_key(...)
        for attr in self._get_filtered_attribute_list():
            # append string
            attr_str_lines = str(
                getattr(self, "_%s_value_" % attr.name)).splitlines()
            if len(attr_str_lines) > 1:
                text += '* %s :\n' % attr.name
                for attr_str in attr_str_lines:
                    text += '    %s\n' % attr_str
            else:
                text += '* %s : %s\n' % (attr.name, attr_str_lines[0])
        return text

    def read(self, stream, data):
        """Read structure from stream."""
        # read all attributes
        value = struct.unpack(data._byte_order + self._struct,
                              stream.read(self._numbytes))[0]
        # set the structure variables
        self.from_int(value, data)

    def from_int(self, value, data):
        """Set structure values from integer."""
        bitpos = 0
        for attr in self._get_filtered_attribute_list(data):
            #print(attr.name) # debug
            attrvalue = (value >> bitpos) & ((1 << attr.numbits) - 1)
            setattr(self, attr.name, attrvalue)
            bitpos += attr.numbits

    def to_int(self, data):
        # implementation note: not defined via __int__ because conversion
        # takes arguments
        """Get as integer."""
        value = 0
        bitpos = 0
        for attr in self._get_filtered_attribute_list(data):
            attrvalue = getattr(self, attr.name)
            value |= (attrvalue & ((1 << attr.numbits) - 1)) << bitpos
            bitpos += attr.numbits
        return value

    def write(self, stream, data):
        """Write structure to stream."""
        stream.write(struct.pack(data._byte_order + self._struct,
                                 self.to_int(data)))

    def fix_links(self, data):
        """Fix links in the structure."""
        return

    def get_links(self, data=None):
        """Get list of all links in the structure."""
        return []

    def get_strings(self, data):
        """Get list of all strings in the structure."""
        return []

    def get_refs(self, data=None):
        """Get list of all references in the structure. Refs are
        links that point down the tree. For instance, if you need to parse
        the whole tree starting from the root you would use get_refs and not
        get_links, as get_links could result in infinite recursion."""
        return []

    def get_size(self, data=None):
        """Calculate the structure size in bytes."""
        return self._numbytes

    def get_hash(self, data=None):
        """Calculate a hash for the structure, as a tuple."""
        # calculate hash
        hsh = []
        for attr in self._get_filtered_attribute_list(data):
            hsh.append(getattr(self, attr.name))
        return tuple(hsh)

    @classmethod
    def get_games(cls):
        """Get games for which this block is supported."""
        return list(cls._games.iterkeys())

    @classmethod
    def get_versions(cls, game):
        """Get versions supported for C{game}."""
        return cls._games[game]

    @classmethod
    def _get_attribute_list(cls):
        """Calculate the list of all attributes of this structure."""
        # string of attributes of base classes of cls
        attrs = []
        for base in cls.__bases__:
            try:
                attrs.extend(base._get_attribute_list())
            except AttributeError: # when base class is "object"
                pass
        attrs.extend(cls._attrs)
        return attrs

    @classmethod
    def _get_names(cls):
        """Calculate the list of all attributes names in this structure.
        Skips duplicate names."""
        # string of attributes of base classes of cls
        names = []
        #for base in cls.__bases__:
        #    try:
        #        names.extend(base._get_names())
        #    except AttributeError: # when base class is "object"
        #        pass
        for attr in cls._attrs:
            if attr.name in names:
                continue
            else:
                names.append(attr.name)
        return names

    def _get_filtered_attribute_list(self, data=None):
        """Generator for listing all 'active' attributes, that is,
        attributes whose condition evaluates ``True``, whose version
        interval contaions C{version}, and whose user version is
        C{user_version}. ``None`` for C{version} or C{user_version} means
        that these checks are ignored. Duplicate names are skipped as
        well.

        Note: Use data instead of version and user_version (old way will be
        deprecated)."""
        names = []
        if data:
            version = data.version
            user_version = data.user_version
        else:
            version = None
            user_version = None
        for attr in self._attribute_list:
            #print(attr.name, version, attr.ver1, attr.ver2) # debug

            # check version
            if not (version is None):
                if (not (attr.ver1 is None)) and version < attr.ver1:
                    continue
                if (not (attr.ver2 is None)) and version > attr.ver2:
                    continue
            #print("version check passed") # debug

            # check user version
            if not(attr.userver is None or user_version is None) \
               and user_version != attr.userver:
                continue
            #print("user version check passed") # debug

            # check condition
            if not (attr.cond is None) and not attr.cond.eval(self):
                continue
            #print("condition passed") # debug

            # skip dupiclate names
            if attr.name in names:
                continue
            #print("duplicate check passed") # debug

            names.append(attr.name)
            # passed all tests
            # so yield the attribute
            yield attr

    def get_attribute(self, name):
        """Get a basic attribute."""
        return getattr(self, "_" + name + "_value_").get_value()

    # important note: to apply partial(set_attribute, name = 'xyz') the
    # name argument must be last
    def set_attribute(self, value, name):
        """Set the value of a basic attribute."""
        getattr(self, "_" + name + "_value_").set_value(value)

    def tree(self):
        """A generator for parsing all blocks in the tree (starting from and
        including C{self}). By default, there is no tree structure, so returns
        self."""
        # return self
        yield self

    # DetailNode

    def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
        """Yield children of this structure."""
        return (item for item in self._items)

    def get_detail_child_names(self, edge_filter=EdgeFilter()):
        """Yield name of each child."""
        return (name for name in self._names)
