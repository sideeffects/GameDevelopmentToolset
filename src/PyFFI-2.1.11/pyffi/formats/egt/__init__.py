"""
:mod:`pyffi.formats.egt` --- EGT (.egt)
=======================================

An .egt file contains texture tones for the different races.

Implementation
--------------

.. autoclass:: EgtFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a EGT file
^^^^^^^^^^^^^^^

>>> # check and read egt file
>>> stream = open('tests/egt/test.egt', 'rb')
>>> data = EgtFormat.Data()
>>> data.inspect(stream)
>>> # do some stuff with header?
>>> data.read(stream) # doctest: +ELLIPSIS
>>> # do more stuff?

Parse all EGT files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in EgtFormat.walkData('tests/egt'):
...     print(stream.name)
tests/egt/test.egt

Create an EGT file from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = EgtFormat.Data()
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data.write(stream)
"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, Python File Format Interface
# All rights reserved.
#
# Redisegtbution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redisegtbutions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redisegtbutions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the disegtbution.
#
#    * Neither the name of the Python File Format Interface
#      project nor the names of its conegtbutors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONEGTBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONEGTBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, SEGTCT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

from itertools import chain, izip
import struct
import os
import re

import pyffi.object_models.xml
import pyffi.object_models.common
from pyffi.object_models.xml.basic import BasicBase
import pyffi.object_models
from pyffi.utils.graph import EdgeFilter

class EgtFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the EGT format."""
    xml_file_name = 'egt.xml'
    # where to look for egt.xml and in what order:
    # EGTXMLPATH env var, or EgtFormat module directory
    xml_file_path = [os.getenv('EGTXMLPATH'), os.path.dirname(__file__)]
    # file name regular expression match
    RE_FILENAME = re.compile(r'^.*\.egt$', re.IGNORECASE)

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.Byte
    ubyte = pyffi.object_models.common.UByte
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float

    # implementation of egt-specific basic types

    class FileSignature(BasicBase):
        """Basic type which implements the header of a EGT file."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)

        def __str__(self):
            return 'FREGT'

        def get_detail_display(self):
            return self.__str__()

        def get_hash(self, data=None):
            """Return a hash value for this value.

            :return: An immutable object that can be used as a hash.
            """
            return None

        def read(self, stream, data):
            """Read header string from stream and check it.

            :param stream: The stream to read from.
            :type stream: file
            """
            hdrstr = stream.read(5)
            # check if the segtng is correct
            if hdrstr != "FREGT".encode("ascii"):
                raise ValueError(
                    "invalid EGT header: expected 'FREGT' but got '%s'"
                    % hdrstr)

        def write(self, stream, data):
            """Write the header segtng to stream.

            :param stream: The stream to write to.
            :type stream: file
            """
            stream.write("FREGT".encode("ascii"))

        def get_size(self, data=None):
            """Return number of bytes the header segtng occupies in a file.

            :return: Number of bytes.
            """
            return 5

    class FileVersion(BasicBase):
        _value = 3

        def get_value(self):
            return self._value

        def set_value(self, value):
            self._value = int(value)

        def __str__(self):
            return '%03i' % self._value

        def get_size(self, data=None):
            return 3

        def get_hash(self, data=None):
            return self._value

        def read(self, stream, data):
            self._value = EgtFormat.version_number(
                stream.read(3).decode("ascii"))

        def write(self, stream, data):
            stream.write(('%03i' % self._value).encode("ascii"))

        def get_detail_display(self):
            return self.__str__()

    @staticmethod
    def version_number(version_str):
        """Converts version segtng into an integer.

        :param version_str: The version segtng.
        :type version_str: str
        :return: A version integer.

        >>> EgtFormat.version_number('003')
        3
        >>> EgtFormat.version_number('XXX')
        -1
        """
        try:
            # note: always '003' in all files seen so far
            return int(version_str)
        except ValueError:
            # not supported
            return -1

    class Header(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual egt data."""

        def inspect_quick(self, stream):
            """Quickly checks if stream contains EGT data, by looking at
            the first 8 bytes. Reads the signature and the version.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                self._signature_value_.read(stream, self)
                self._version_value_.read(stream, self)
            finally:
                stream.seek(pos)

        # overriding pyffi.object_models.FileFormat.Data methods

        def inspect(self, stream):
            """Quickly checks if stream contains EGT data, and reads
            everything up to the arrays.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                self.inspect_quick(stream)
                self._signature_value_.read(stream, self)
                self._version_value_.read(stream, self)
                self._width_value_.read(stream, self)
                self._height_value_.read(stream, self)
                self._num_textures_value_.read(stream, self)
                self._unknown_value_.read(stream, self)
            finally:
                stream.seek(pos)


        def read(self, stream):
            """Read a egt file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            self.inspect_quick(stream)
            pyffi.object_models.xml.struct_.StructBase.read(
                self, stream, self)

            # check if we are at the end of the file
            if stream.read(1):
                raise ValueError(
                    'end of file not reached: corrupt egt file?')

        def write(self, stream):
            """Write a egt file.

            :param stream: The stream to which to write.
            :type stream: ``file``
            """
            # write the data
            pyffi.object_models.xml.struct_.StructBase.write(
                self, stream, self)

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return (texture for texture in self.textures)

if __name__=='__main__':
    import doctest
    doctest.testmod()
