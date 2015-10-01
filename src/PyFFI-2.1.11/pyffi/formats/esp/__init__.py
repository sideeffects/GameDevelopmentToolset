"""
:mod:`pyffi.formats.esp` --- Elder Scrolls plugin/master/save files (.esp, .esm, and .ess)
==========================================================================================

Implementation
--------------

.. autoclass:: EspFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a ESP file
^^^^^^^^^^^^^^^

>>> # check and read esp file
>>> stream = open('tests/esp/test.esp', 'rb')
>>> data = EspFormat.Data()
>>> data.inspect(stream)
>>> # do some stuff with header?
>>> #data.header....
>>> data.read(stream)
>>> # do some stuff...

Parse all ESP files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in EspFormat.walkData('tests/esp'):
...     print(stream.name)
tests/esp/test.esp

Create an ESP file from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = EspFormat.Data()
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data.write(stream)
"""

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

import struct
import os
import re

import pyffi.object_models.xml
import pyffi.object_models.common
from pyffi.object_models.xml.basic import BasicBase
import pyffi.object_models
from pyffi.utils.graph import EdgeFilter

class EspFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the ESP format."""
    xml_file_name = 'esp.xml'
    # where to look for esp.xml and in what order:
    # ESPXMLPATH env var, or EspFormat module directory
    xml_file_path = [os.getenv('ESPXMLPATH'), os.path.dirname(__file__)]
    # filter for recognizing esp files by extension
    # .ess are users save games encoded similarly to esp files 
    # .esm are esp files with an bit set in the header.
    RE_FILENAME = re.compile(r'^.*\.(esp|ess|esm)$', re.IGNORECASE)
    # used for comparing floats
    _EPSILON = 0.0001

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.Byte
    ubyte = pyffi.object_models.common.UByte
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float
    uint64 = pyffi.object_models.common.UInt64
    ZString = pyffi.object_models.common.ZString
    class RecordType(pyffi.object_models.common.FixedString):
        _len = 4

    # implementation of esp-specific basic types

    # XXX nothing here yet...

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.

        :param version_str: The version string.
        :type version_str: str
        :return: A version integer.

        >>> hex(EspFormat.version_number('1.2'))
        '0x102'
        """
        high, low = version_str.split(".")
        return (int(high) << 8) + int(low)

    @classmethod
    def _read_records(cls, stream, data,
                      parent=None, size=None, num_records=None):
        """Read records by data size or by number."""
        records = []
        while (size > 0) if size is not None else (num_records > 0):
            pos = stream.tell()
            record_type = stream.read(4).decode()
            if parent:
                record_type = parent.__class__.__name__ + "_" + record_type
            stream.seek(pos)
            try:
                record = getattr(cls, record_type)()
            except AttributeError:
                print("unknown record type %s; aborting" % record_type)
                break
            records.append(record)
            record.read(stream, data)
            if size is not None:
                size -= stream.tell() - pos #slower: record.get_size()
            else:
                num_records -= 1
        return records

    class Data(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual esp data."""
        def __init__(self):
            self.tes4 = EspFormat.TES4()
            self.records = []

        def inspect_quick(self, stream):
            """Quickly checks if stream contains ESP data, and gets the
            version, by looking at the first 8 bytes.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                # XXX check that file is ESP
                if (stream.read(4) != 'TES4'):
                    raise ValueError("Not an ESP file.")
            finally:
                stream.seek(pos)

        # overriding pyffi.object_models.FileFormat.Data methods

        def inspect(self, stream):
            """Quickly checks if stream contains ESP data, and reads the
            header.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                self.inspect_quick(stream)
                # XXX read header
            finally:
                stream.seek(pos)


        def read(self, stream):
            """Read a esp file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            self.inspect_quick(stream)
            # read header record
            self.tes4.read(stream, self)
            hedr = self.tes4.get_sub_record("HEDR")
            if not hedr:
                print("esp file has no HEDR; aborting")
                return
            self.records = EspFormat._read_records(
                stream, self, num_records=hedr.num_records)

            # check if we are at the end of the file
            if stream.read(1):
                #raise ValueError(
                print(
                    'end of file not reached: corrupt esp file?')
            
        def write(self, stream):
            """Write a esp file.

            :param stream: The stream to which to write.
            :type stream: ``file``
            """
            self.tes4.write(stream, self)

        # DetailNode

        def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
            return self.tes4.get_detail_child_nodes(edge_filter=edge_filter)

        def get_detail_child_names(self, edge_filter=EdgeFilter()):
            return self.tes4.get_detail_child_names(edge_filter=edge_filter)

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return self.tes4.sub_records + self.records

    class Record:
        def __init__(self):
            pyffi.object_models.xml.struct_.StructBase.__init__(self)
            self.sub_records = []

        def read(self, stream, data):
            # read all fields
            pyffi.object_models.xml.struct_.StructBase.read(
                self, stream, data)
            # read all subrecords
            self.sub_records = EspFormat._read_records(
                stream, data, parent=self, size=self.data_size)

        def write(self, stream, data):
            raise NotImplementedError

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return self.sub_records

        # other functions

        def get_sub_record(self, sub_record_type):
            """Find first subrecord of given type."""
            for sub_record in self.sub_records:
                if sub_record.type == sub_record_type:
                    return sub_record
            # not found
            return None

    class GRUP:
        def __init__(self):
            pyffi.object_models.xml.struct_.StructBase.__init__(self)
            self.records = []

        def read(self, stream, data):
            # read all fields
            pyffi.object_models.xml.struct_.StructBase.read(
                self, stream, data)
            # read all subrecords
            self.records = EspFormat._read_records(
                stream, data, size=self.data_size - 20)

        def write(self, stream, data):
            raise NotImplementedError

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return self.records
