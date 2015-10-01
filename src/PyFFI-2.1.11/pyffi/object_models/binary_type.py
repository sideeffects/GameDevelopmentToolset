"""Implements common basic types in XML file format descriptions."""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, Python File Format Interface.
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

import struct

from pyffi.object_models.any_type import AnyType
from pyffi.object_models.simple_type import SimpleType
from pyffi.object_models.editable import EditableSpinBox
from pyffi.object_models.editable import EditableFloatSpinBox
from pyffi.object_models.editable import EditableLineEdit
from pyffi.object_models.editable import EditableBoolComboBox

# Base classes

class BinaryType(AnyType):
    """Abstract base class for binary data types."""
    def get_size(self):
        raise NotImplementedError

class BinarySimpleType(SimpleType, BinaryType):
    """Abstract base class for binary data types."""
    pass

# Helper objects and helper functions (private)

_b = "".encode("ascii") # py3k's b""
_b00 = "\x00".encode("ascii") # py3k's b"\x00"


# supports the bytes object for < py26
try:
    bytes
except NameError:
    bytes = str # for py25 backwards compatibility

if bytes is str:
    # < py3k: str for byte strings, unicode for text strings
    _bytes = str
    _str = unicode
else:
    # >= py3k: bytes for byte strings, str for text strings
    _bytes = bytes
    _str = str

def _as_bytes(value):
    """Helper function which converts a string to _bytes (this is useful for
    set_value in all string classes, which use bytes for representation).

    :return: The bytes representing the value.
    :rtype: C{_bytes}

    >>> # following doctest fails on py3k, hence disabled
    >>> _as_bytes(u"\\u00e9defa") == u"\\u00e9defa".encode("utf-8") # doctest: +SKIP
    True

    >>> _as_bytes(123) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...
    """
    if isinstance(value, _bytes):
        return value
    elif isinstance(value, _str):
        return value.encode("utf-8", "replace")
    else:
        raise TypeError("expected %s or %s" % (_bytes.__name__, _str.__name__))

def _as_str(value):
    """Helper function to convert bytes back to str. This is used in
    the __str__ functions for simple string types. If you want a custom
    encoding, use an explicit decode call on the value.
    """
    if not isinstance(value, (_str, _bytes)):
        raise TypeError("expected %s or %s" % (_bytes.__name__, _str.__name__))
    elif not value:
        return ''
    elif isinstance(value, str):
        # this always works regardless of the python version
        return value
    elif isinstance(value, _bytes):
        # >= py3k: simply decode
        return value.decode("utf-8", "replace")
    elif isinstance(value, unicode):
        # < py3k: use ascii encoding to produce a str
        # (this avoids unicode errors)
        return value.encode("ascii", "replace")

# SimpleType implementations for common binary types

class IntType(BinarySimpleType, EditableSpinBox):
    """Basic implementation of a 32-bit signed integer type. Also serves as a
    base class for all other integer types.

    >>> from tempfile import TemporaryFile
    >>> tmp = TemporaryFile()
    >>> i = IntType()
    >>> i.value = -1
    >>> i.value
    -1
    >>> i.value = 0x11223344
    >>> i.write(tmp)
    >>> j = IntType()
    >>> if tmp.seek(0): pass # ignore result for py3k
    >>> j.read(tmp)
    >>> hex(j.value)
    '0x11223344'
    >>> i.value = 2**40 # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> i.value = 'hello world'
    Traceback (most recent call last):
        ...
    ValueError: cannot convert value 'hello world' to integer
    >>> if tmp.seek(0): pass # ignore result for py3k
    >>> if tmp.write('\x11\x22\x33\x44'.encode("ascii")): pass # b'\x11\x22\x33\x44'
    >>> if tmp.seek(0): pass # ignore result for py3k
    >>> i.read(tmp)
    >>> hex(i.value)
    '0x44332211'
    """

    _min = -0x80000000 #: Minimum value.
    _max = 0x7fffffff  #: Maximum value.
    _struct = 'i'      #: Character used to represent type in struct.
    _size = 4          #: Number of bytes.

    # SimpleType

    def __init__(self):
        """Initialize the integer."""
        self._value = 0

    def set_value(self, value):
        """Set value to C{value}. Calls C{int(value)} to convert to integer.

        :param value: The value to assign.
        :type value: int
        """
        try:
            val = int(value)
        except ValueError:
            try:
                val = int(value, 16) # for '0x...' strings
            except ValueError:
                try:
                    val = getattr(self, value) # for enums
                except AttributeError:
                    raise ValueError(
                        "cannot convert value '%s' to integer"%value)
        if val < self._min or val > self._max:
            raise ValueError('value out of range (%i)' % val)
        self._value = val

    # AnyType

    def read(self, stream):
        """Read value from stream.

        :param stream: The stream to read from.
        :type stream: ``file``
        """
        self._value = struct.unpack('<' + self._struct,
                                    stream.read(self._size))[0]

    def write(self, stream):
        """Write value to stream.

        :param stream: The stream to write to.
        :type stream: ``file``
        """
        stream.write(struct.pack('<' + self._struct, self._value))

    # BinaryType

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return self._size

    # EditableSpinBox

    def get_editor_minimum(self):
        """Minimum possible value.

        :return: Minimum possible value.
        """
        return self._min

    def get_editor_maximum(self):
        """Maximum possible value.

        :return: Maximum possible value.
        """
        return self._max

class UIntType(IntType):
    """Implementation of a 32-bit unsigned integer type."""
    _min = 0
    _max = 0xffffffff
    _struct = 'I'
    _size = 4

class ByteType(IntType):
    """Implementation of a 8-bit signed integer type."""
    _min = -0x80
    _max = 0x7f
    _struct = 'b'
    _size = 1

class UByteType(IntType):
    """Implementation of a 8-bit unsigned integer type."""
    _min = 0
    _max = 0xff
    _struct = 'B'
    _size = 1

class ShortType(IntType):
    """Implementation of a 16-bit signed integer type."""
    _min = -0x8000
    _max = 0x7fff
    _struct = 'h'
    _size = 2

class UShortType(UIntType):
    """Implementation of a 16-bit unsigned integer type."""
    _min = 0
    _max = 0xffff
    _struct = 'H'
    _size = 2

class BoolType(UByteType, EditableBoolComboBox):
    """Simple bool implementation."""

    def get_value(self):
        """Return stored value.

        :return: The stored value.
        """
        return bool(self._value)

    def set_value(self, value):
        """Set value to C{value}.

        :param value: The value to assign.
        :type value: bool
        """
        if not isinstance(value, bool):
            raise TypeError("expected a bool")
        self._value = 1 if value else 0

class CharType(BinarySimpleType, EditableLineEdit):
    """Implementation of an (unencoded) 8-bit character."""

    def __init__(self):
        """Initialize the character."""
        self._value = _b00

    def set_value(self, value):
        """Set character to C{value}.

        :param value: The value to assign (bytes of length 1).
        :type value: bytes
        """
        assert(isinstance(value, _bytes))
        assert(len(value) == 1)
        self._value = value

    def read(self, stream):
        """Read value from stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        self._value = stream.read(1)

    def write(self, stream):
        """Write value to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(self._value)

    def __str__(self):
        return _as_str(self._value)

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return 1

class Float(BinarySimpleType, EditableFloatSpinBox):
    """Implementation of a 32-bit float."""

    def __init__(self):
        """Initialize the float."""
        self._value = 0.0

    def set_value(self, value):
        """Set value to C{value}.

        :param value: The value to assign.
        :type value: float
        """
        self._value = float(value)

    def read(self, stream):
        """Read value from stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        self._value = struct.unpack('<f', stream.read(4))[0]

    def write(self, stream):
        """Write value to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(struct.pack('<f', self._value))

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return 4

class ZString(BinarySimpleType, EditableLineEdit):
    """String of variable length (null terminated).

    >>> from tempfile import TemporaryFile
    >>> f = TemporaryFile()
    >>> s = ZString()
    >>> if f.write('abcdefghijklmnopqrst\\x00'.encode("ascii")): pass # b'abc...'
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.read(f)
    >>> str(s)
    'abcdefghijklmnopqrst'
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.value = 'Hi There!'
    >>> s.write(f)
    >>> if f.seek(0): pass # ignore result for py3k
    >>> m = ZString()
    >>> m.read(f)
    >>> str(m)
    'Hi There!'
    """
    _maxlen = 1000 #: The maximum length.

    def __init__(self):
        """Initialize the string."""
        self._value = _b

    def __str__(self):
        return _as_str(self._value)

    def set_value(self, value):
        """Set string to C{value}.

        :param value: The value to assign.
        :type value: ``str`` (will be encoded as default) or C{bytes}
        """
        val = _as_bytes(value)
        i = val.find(_b00)
        if i != -1:
            val = val[:i]
        if len(val) > self._maxlen:
            raise ValueError('string too long')
        self._value = val

    def read(self, stream):
        """Read string from stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        i = 0
        val = _b
        char = _b
        while char != _b00:
            i += 1
            if i > self._maxlen:
                raise ValueError('string too long')
            val += char
            char = stream.read(1)
        self._value = val

    def write(self, stream):
        """Write string to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(self._value)
        stream.write(_b00)

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return len(self._value) + 1

class FixedString(BinarySimpleType, EditableLineEdit):
    """String of fixed length. Default length is 0, so you must override
    this class and set the _len class variable.

    >>> from tempfile import TemporaryFile
    >>> f = TemporaryFile()
    >>> class String8(FixedString):
    ...     _len = 8
    >>> s = String8()
    >>> if f.write('abcdefghij'.encode()): pass # ignore result for py3k
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.read(f)
    >>> str(s)
    'abcdefgh'
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.value = 'Hi There'
    >>> s.write(f)
    >>> if f.seek(0): pass # ignore result for py3k
    >>> m = String8()
    >>> m.read(f)
    >>> str(m)
    'Hi There'
    """
    _len = 0

    def __init__(self):
        """Initialize the string."""
        self._value = _b

    def __str__(self):
        return _as_str(self._value)

    def get_value(self):
        """Return the string.

        :return: The stored string.
        :rtype: C{bytes}
        """
        return self._value

    def set_value(self, value):
        """Set string to C{value}.

        :param value: The value to assign.
        :type value: ``str`` (encoded as default) or C{bytes}
        """
        val = _as_bytes(value)
        if len(val) > self._len:
            raise ValueError("string '%s' too long" % val)
        self._value = val

    def read(self, stream):
        """Read string from stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        self._value = stream.read(self._len)
        i = self._value.find(_b00)
        if i != -1:
            self._value = self._value[:i]

    def write(self, stream):
        """Write string to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(self._value.ljust(self._len, _b00))

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return self._len

class SizedString(BinarySimpleType, EditableLineEdit):
    """Basic type for strings. The type starts with an unsigned int which
    describes the length of the string.

    >>> from tempfile import TemporaryFile
    >>> f = TemporaryFile()
    >>> s = SizedString()
    >>> if f.write('\\x07\\x00\\x00\\x00abcdefg'.encode("ascii")): pass # ignore result for py3k
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.read(f)
    >>> str(s)
    'abcdefg'
    >>> if f.seek(0): pass # ignore result for py3k
    >>> s.set_value('Hi There')
    >>> s.write(f)
    >>> if f.seek(0): pass # ignore result for py3k
    >>> m = SizedString()
    >>> m.read(f)
    >>> str(m)
    'Hi There'
    """

    def __init__(self):
        """Initialize the string."""
        self._value = _b

    def get_value(self):
        """Return the string.

        :return: The stored string.
        """
        return self._value

    def set_value(self, value):
        """Set string to C{value}.

        :param value: The value to assign.
        :type value: str
        """
        val = _as_bytes(value)
        if len(val) > 10000:
            raise ValueError('string too long')
        self._value = val

    def __str__(self):
        return _as_str(self._value)

    def get_size(self):
        """Return number of bytes this type occupies in a file.

        :return: Number of bytes.
        """
        return 4 + len(self._value)

    def read(self, stream):
        """Read string from stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        length, = struct.unpack('<I', stream.read(4))
        if length > 10000:
            raise ValueError('string too long (0x%08X at 0x%08X)'
                             % (length, stream.tell()))
        self._value = stream.read(length)

    def write(self, stream):
        """Write string to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(struct.pack('<I', len(self._value)))
        stream.write(self._value)

class UndecodedData(SimpleType, BinaryType):
    """Basic type for undecoded data trailing at the end of a file."""
    def __init__(self):
        self._value = _b

    def get_value(self):
        """Return stored value.

        :return: The stored value.
        """
        return self._value

    def set_value(self, value):
        """Set value to C{value}.

        :param value: The value to assign.
        :type value: bytes
        """
        if len(value) > 16000000:
            raise ValueError('data too long')
        self._value = value

    def __str__(self):
        return '<UNDECODED DATA>'

    def get_size(self):
        """Return number of bytes the data occupies in a file.

        :return: Number of bytes.
        """
        return len(self._value)

    def read(self, stream):
        """Read data from stream. Note that this function simply
        reads until the end of the stream.

        :param stream: The stream to read from.
        :type stream: file
        """
        self._value = stream.read(-1)

    def write(self, stream):
        """Write data to stream.

        :param stream: The stream to write to.
        :type stream: file
        """
        stream.write(self._value)
