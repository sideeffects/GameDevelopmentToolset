"""
:mod:`pyffi.formats.kfm` --- NetImmerse/Gamebryo Keyframe Motion (.kfm)
=======================================================================

Implementation
--------------

.. autoclass:: KfmFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a KFM file
^^^^^^^^^^^^^^^

>>> # read kfm file
>>> stream = open('tests/kfm/test.kfm', 'rb')
>>> data = KfmFormat.Data()
>>> data.inspect(stream)
>>> print(data.nif_file_name.decode("ascii"))
Test.nif
>>> data.read(stream)
>>> stream.close()
>>> # get all animation file names
>>> for anim in data.animations:
...     print(anim.kf_file_name.decode("ascii"))
Test_MD_Idle.kf
Test_MD_Run.kf
Test_MD_Walk.kf
Test_MD_Die.kf

Parse all KFM files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in KfmFormat.walkData('tests/kfm'):
...     print(stream.name)
tests/kfm/test.kfm

Create a KFM model from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = KfmFormat.Data()
>>> data.nif_file_name = "Test.nif"
>>> data.num_animations = 4
>>> data.animations.update_size()
>>> data.animations[0].kf_file_name = "Test_MD_Idle.kf"
>>> data.animations[1].kf_file_name = "Test_MD_Run.kf"
>>> data.animations[2].kf_file_name = "Test_MD_Walk.kf"
>>> data.animations[3].kf_file_name = "Test_MD_Die.kf"
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data.write(stream)
>>> stream.close()

Get list of versions and games
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for vnum in sorted(KfmFormat.versions.values()):
...     print('0x%08X' % vnum)
0x01000000
0x01024B00
0x0200000B
0x0201000B
0x0202000B
>>> for game, versions in sorted(KfmFormat.games.items(),
...                              key=lambda x: x[0]):
...     print("%s " % game + " ".join('0x%08X' % vnum for vnum in versions))
Civilization IV 0x01000000 0x01024B00 0x0200000B
Emerge 0x0201000B 0x0202000B
Loki 0x01024B00
Megami Tensei: Imagine 0x0201000B
Oblivion 0x01024B00
Prison Tycoon 0x01024B00
Pro Cycling Manager 0x01024B00
Red Ocean 0x01024B00
Sid Meier's Railroads 0x0200000B
The Guild 2 0x01024B00
"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, NIF File Format Library and Tools.
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
#    * Neither the name of the NIF File Format Library and Tools
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

import struct, os, re

import pyffi.object_models.xml
import pyffi.object_models.common
from pyffi.object_models.xml.basic import BasicBase
from pyffi.utils.graph import EdgeFilter
import pyffi.object_models
import pyffi.object_models.xml.struct_

class KfmFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the kfm file format."""
    xml_file_name = 'kfm.xml'
    # where to look for kfm.xml and in what order:
    # KFMXMLPATH env var, or KfmFormat module directory
    xml_file_path = [os.getenv('KFMXMLPATH'),
                     os.path.join(os.path.dirname(__file__), "kfmxml")]
    # file name regular expression match
    RE_FILENAME = re.compile(r'^.*\.kfm$', re.IGNORECASE)
    # used for comparing floats
    _EPSILON = 0.0001

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.UByte # not a typo
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float
    SizedString = pyffi.object_models.common.SizedString
    TextString = pyffi.object_models.common.UndecodedData # for text (used by older kfm versions)

    # implementation of kfm-specific basic types

    class HeaderString(BasicBase):
        """The kfm header string."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self._doseol = False

        def __str__(self):
            return ';Gamebryo KFM File Version x.x.x.x'

        def get_hash(self, data=None):
            """Return a hash value for this value.

            :return: An immutable object that can be used as a hash.
            """
            return None

        def read(self, stream, data):
            """Read header string from stream and check it.

            :param stream: The stream to read from.
            :type stream: file
            :keyword version: The file version.
            :type version: int
            """
            # get the string we expect
            version_string = self.version_string(data.version)
            # read string from stream
            hdrstr = stream.read(len(version_string))
            # check if the string is correct
            if hdrstr != version_string.encode("ascii"):
                raise ValueError(
                    "invalid KFM header: expected '%s' but got '%s'"
                    % (version_string, hdrstr))
            # check eol style
            nextchar = stream.read(1)
            if nextchar == '\x0d'.encode("ascii"):
                nextchar = stream.read(1)
                self._doseol = True
            else:
                self._doseol = False
            if nextchar != '\x0a'.encode("ascii"):
                raise ValueError(
                    "invalid KFM header: string does not end on \\n or \\r\\n")

        def write(self, stream, data):
            """Write the header string to stream.

            :param stream: The stream to write to.
            :type stream: file
            """
            # write the version string
            stream.write(self.version_string(data.version).encode("ascii"))
            # write \n (or \r\n for older versions)
            if self._doseol:
                stream.write('\x0d\x0a'.encode("ascii"))
            else:
                stream.write('\x0a'.encode("ascii"))

        def get_size(self, data=None):
            """Return number of bytes the header string occupies in a file.

            :return: Number of bytes.
            """
            return len(self.version_string(data.version)) \
                   + (1 if not self._doseol else 2)

        # DetailNode

        def get_detail_display(self):
            return str(self)

        @staticmethod
        def version_string(version):
            """Transforms version number into a version string.

            :param version: The version number.
            :type version: int
            :return: A version string.

            >>> KfmFormat.HeaderString.version_string(0x0202000b)
            ';Gamebryo KFM File Version 2.2.0.0b'
            >>> KfmFormat.HeaderString.version_string(0x01024b00)
            ';Gamebryo KFM File Version 1.2.4b'
            """
            if version == -1 or version is None:
                raise RuntimeError('no string for version %s'%version)
            return ";Gamebryo KFM File Version %s"%({
                0x01000000 : "1.0",
                0x01024b00 : "1.2.4b",
                0x0200000b : "2.0.0.0b",
                0x0201000b : "2.1.0.0b",
                0x0202000b : "2.2.0.0b" } [version])

    # other types with internal implementation
    class FilePath(SizedString):
        def get_hash(self, data=None):
            """Return a hash value for this value.
            For file paths, the hash value is case insensitive.

            :return: An immutable object that can be used as a hash.
            """
            return self.get_value().lower()

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.

        :param version_str: The version string.
        :type version_str: str
        :return: A version integer.

        >>> hex(KfmFormat.version_number('1.0'))
        '0x1000000'
        >>> hex(KfmFormat.version_number('1.2.4b'))
        '0x1024b00'
        >>> hex(KfmFormat.version_number('2.2.0.0b'))
        '0x202000b'
        """

        if not '.' in version_str:
            return int(version_str)

        try:
            ver_list = [int(x, 16) for x in version_str.split('.')]
        except ValueError:
            # version not supported (i.e. version_str '10.0.1.3z' would
            # trigger this)
            return -1
        if len(ver_list) > 4 or len(ver_list) < 1:
            # version not supported
            return -1
        for ver_digit in ver_list:
            if (ver_digit | 0xff) > 0xff:
                return -1 # version not supported
        while len(ver_list) < 4:
            ver_list.append(0)
        return ((ver_list[0] << 24)
                + (ver_list[1] << 16)
                + (ver_list[2] << 8)
                + ver_list[3])

    class Header(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual kfm data."""
        version = 0x01024B00

        def inspect(self, stream):
            """Quick heuristic check if stream contains KFM data,
            by looking at the first 64 bytes. Sets version and reads
            header string.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                hdrstr = stream.readline(64).rstrip()
            finally:
                stream.seek(pos)
            if hdrstr.startswith(";Gamebryo KFM File Version ".encode("ascii")):
                version_str = hdrstr[27:].decode("ascii")
            else:
                # not a kfm file
                raise ValueError("Not a KFM file.")
            try:
                ver = KfmFormat.version_number(version_str)
            except:
                # version not supported
                raise ValueError("KFM version not supported.")
            if not ver in KfmFormat.versions.values():
                # unsupported version
                raise ValueError("KFM version not supported.")
            # store version
            self.version = ver
            # read header string
            try:
                self._header_string_value_.read(stream, self)
                self._unknown_byte_value_.read(stream, self)
                self._nif_file_name_value_.read(stream, self)
                self._master_value_.read(stream, self)
            finally:
                stream.seek(pos)

        def read(self, stream):
            """Read a kfm file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            # read the file
            self.inspect(stream) # quick check
            pyffi.object_models.xml.struct_.StructBase.read(
                self, stream, self)

            # check if we are at the end of the file
            if stream.read(1):
                raise ValueError('end of file not reached: corrupt kfm file?')

        def write(self, stream):
            """Write a kfm file.

            :param stream: The stream to which to write.
            :type stream: ``file``
            """
            # write the file
            pyffi.object_models.xml.struct_.StructBase.write(
                self, stream, self)

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return (anim for anim in self.animations)

        def get_global_display(self):
            """Display the nif file name."""
            return self.nif_file_name

    class Animation:
        # XXX this does not work yet (see todo for KfmFormat)
        def get_detail_display(self):
            """Display the kf file name."""
            return self.kf_file_name if not self.name else self.name

        def get_global_display(self):
            """Display the kf file name."""
            return self.kf_file_name if not self.name else self.name
