"""Abstract base class for implementing xml enum types."""

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

import logging
import struct
from itertools import izip

from pyffi.object_models.xml.basic import BasicBase
from pyffi.object_models.editable import EditableComboBox

class _MetaEnumBase(type):
    """This metaclass checks for the presence of _enumkeys, _enumvalues,
    and _numbytes attributes. It also adds enum class attributes.

    Used as metaclass of EnumBase."""
    def __init__(cls, name, bases, dct):
        super(_MetaEnumBase, cls).__init__(name, bases, dct)
        # consistency checks
        if not '_enumkeys' in dct:
            raise TypeError('%s: missing _enumkeys attribute'%cls)
        if not '_enumvalues' in dct:
            raise TypeError('%s: missing _enumvalues attribute'%cls)
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
            raise RuntimeError("unsupported enum numbytes")

        # template type?
        cls._is_template = False
        # does the type contain a Ref or a Ptr?
        cls._has_links = False
        # does the type contain a Ref?
        cls._has_refs = False
        # does the type contain a string?
        cls._has_strings = False

        # for other read/write checking
        cls._min = 0
        cls._max = (1 << (cls._numbytes * 8)) - 1

        # set enum values as class attributes
        for item, value in izip(cls._enumkeys, cls._enumvalues):
            setattr(cls, item, value)

class EnumBase(BasicBase, EditableComboBox):
    __metaclass__ = _MetaEnumBase
    _enumkeys = []
    _enumvalues = []
    _numbytes = 1 # default width of an enum

    #
    # BasicBase methods
    #

    def __init__(self, **kwargs):
        super(EnumBase, self).__init__(**kwargs)
        self._value = self._enumvalues[0]

    def get_value(self):
        """Return stored value."""
        return self._value

    def set_value(self, value):
        """Set value to C{value}."""
        try:
            val = int(value)
        except ValueError:
            try:
                val = int(value, 16) # for '0x...' strings
            except ValueError:
                if value in self._enumkeys:
                    val = getattr(self, value)
                else:
                    raise ValueError(
                        "cannot convert value '%s' to integer"%value)
        if not val in self._enumvalues:
            logger = logging.getLogger("pyffi.object_models.xml.enum")
            logger.error('invalid enum value (%i)' % val)
        else:
            self._value = val

    def read(self, stream, data):
        """Read value from stream."""
        self._value = struct.unpack(data._byte_order + self._struct,
                                    stream.read(self._numbytes))[0]

    def write(self, stream, data):
        """Write value to stream."""
        stream.write(struct.pack(data._byte_order + self._struct,
                                 self._value))

    def __str__(self):
        try:
            return self._enumkeys[self._enumvalues.index(self.get_value())]
        except ValueError:
            # not in _enumvalues list
            return "<INVALID (%i)>" % self.get_value()

    def get_size(self, data=None):
        """Return size of this type."""
        return self._numbytes

    def get_hash(self, data=None):
        """Return a hash value for this value."""
        return self.get_value()

    #
    # EditableComboBox methods
    #

    def get_editor_keys(self):
        """List or tuple of strings, each string describing an item."""
        return self._enumkeys

    def set_editor_value(self, index):
        """Set value from item index."""
        self.set_value(self._enumvalues[index])

    def get_editor_value(self):
        """Get the item index from the enum value."""
        return self._enumvalues.index(self._value)

    def get_detail_display(self):
        """Return object that can be used to display the instance."""
        try:
            return self._enumkeys[self._enumvalues.index(self._value)]
        except ValueError:
            # value self._value is not in the self._enumvalues list
            return "<INVALID (0x%08X)>" % self._value
