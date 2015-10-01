"""
:mod:`pyffi.formats.tri` --- TRI (.tri)
=======================================

A .tri file contains facial expression data, that is, morphs for dynamic
expressions such as smile, frown, and so on.

Implementation
--------------

.. autoclass:: TriFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a TRI file
^^^^^^^^^^^^^^^

>>> # check and read tri file
>>> stream = open('tests/tri/mmouthxivilai.tri', 'rb')
>>> data = TriFormat.Data()
>>> data.inspect(stream)
>>> # do some stuff with header?
>>> data.num_vertices
89
>>> data.num_tri_faces
215
>>> data.num_quad_faces
0
>>> data.num_uvs
89
>>> data.num_morphs
18
>>> data.read(stream) # doctest: +ELLIPSIS
>>> print([str(morph.name.decode("ascii")) for morph in data.morphs])
['Fear', 'Surprise', 'Aah', 'BigAah', 'BMP', 'ChJSh', 'DST', 'Eee', 'Eh', \
'FV', 'I', 'K', 'N', 'Oh', 'OohQ', 'R', 'Th', 'W']

Parse all TRI files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in TriFormat.walkData('tests/tri'):
...     print(stream.name)
tests/tri/mmouthxivilai.tri

Create an TRI file from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = TriFormat.Data()
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

from itertools import chain, izip
import struct
import os
import re

import pyffi.object_models.xml
import pyffi.object_models.common
from pyffi.object_models.xml.basic import BasicBase
import pyffi.object_models
from pyffi.utils.graph import EdgeFilter

class TriFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the TRI format."""
    xml_file_name = 'tri.xml'
    # where to look for tri.xml and in what order:
    # TRIXMLPATH env var, or TriFormat module directory
    xml_file_path = [os.getenv('TRIXMLPATH'), os.path.dirname(__file__)]
    # file name regular expression match
    RE_FILENAME = re.compile(r'^.*\.tri$', re.IGNORECASE)

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.Byte
    ubyte = pyffi.object_models.common.UByte
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float

    # implementation of tri-specific basic types

    class SizedStringZ(pyffi.object_models.common.SizedString):

        def get_size(self, data=None):
            """Return number of bytes this type occupies in a file.

            :return: Number of bytes.
            """
            return (
                1 +
                pyffi.object_models.common.SizedString.get_size(self, data)
                )

        def read(self, stream, data):
            """Read string from stream.

            :param stream: The stream to read from.
            :type stream: file
            """
            pyffi.object_models.common.SizedString.read(self, stream, data)
            self._value = self._value.rstrip(pyffi.object_models.common._b00)

        def write(self, stream, data):
            """Write string to stream.

            :param stream: The stream to write to.
            :type stream: file
            """
            self._value += pyffi.object_models.common._b00
            pyffi.object_models.common.SizedString.write(self, stream, data)
            self._value = self._value.rstrip(pyffi.object_models.common._b00)

    class FileSignature(BasicBase):
        """Basic type which implements the header of a TRI file."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)

        def __str__(self):
            return 'FRTRI'

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
            # check if the string is correct
            if hdrstr != "FRTRI".encode("ascii"):
                raise ValueError(
                    "invalid TRI header: expected 'FRTRI' but got '%s'"
                    % hdrstr)

        def write(self, stream, data):
            """Write the header string to stream.

            :param stream: The stream to write to.
            :type stream: file
            """
            stream.write("FRTRI".encode("ascii"))

        def get_size(self, data=None):
            """Return number of bytes the header string occupies in a file.

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
            self._value = TriFormat.version_number(
                stream.read(3).decode("ascii"))

        def write(self, stream, data):
            stream.write(('%03i' % self._value).encode("ascii"))

        def get_detail_display(self):
            return self.__str__()

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.

        :param version_str: The version string.
        :type version_str: str
        :return: A version integer.

        >>> TriFormat.version_number('003')
        3
        >>> TriFormat.version_number('XXX')
        -1
        """
        try:
            # note: always '003' in all files seen so far
            return int(version_str)
        except ValueError:
            # not supported
            return -1

    class Header(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual tri data."""

        def inspect_quick(self, stream):
            """Quickly checks if stream contains TRI data, by looking at
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
            """Quickly checks if stream contains TRI data, and reads
            everything up to the arrays.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                self.inspect_quick(stream)
                self._signature_value_.read(stream, self)
                self._version_value_.read(stream, self)
                self._num_vertices_value_.read(stream, self)
                self._num_tri_faces_value_.read(stream, self)
                self._num_quad_faces_value_.read(stream, self)
                self._unknown_1_value_.read(stream, self)
                self._unknown_2_value_.read(stream, self)
                self._num_uvs_value_.read(stream, self)
                self._has_uv_value_.read(stream, self)
                self._num_morphs_value_.read(stream, self)
                self._num_modifiers_value_.read(stream, self)
                self._num_modifier_vertices_value_.read(stream, self)
            finally:
                stream.seek(pos)


        def read(self, stream):
            """Read a tri file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            self.inspect_quick(stream)
            pyffi.object_models.xml.struct_.StructBase.read(
                self, stream, self)

            # check if we are at the end of the file
            if stream.read(1):
                raise ValueError(
                    'end of file not reached: corrupt tri file?')

            # copy modifier vertices into modifier records
            start_index = 0
            for modifier in self.modifiers:
                modifier.modifier_vertices.update_size()
                for src_vert, dst_vert in izip(
                    self.modifier_vertices[
                        start_index:start_index
                        + modifier.num_vertices_to_modify],
                    modifier.modifier_vertices):
                    dst_vert.x = src_vert.x
                    dst_vert.y = src_vert.y
                    dst_vert.z = src_vert.z
                start_index += modifier.num_vertices_to_modify

        def write(self, stream):
            """Write a tri file.

            :param stream: The stream to which to write.
            :type stream: ``file``
            """
            # copy modifier vertices from modifier records to header
            if self.modifiers:
                self.num_modifier_vertices = sum(
                    modifier.num_vertices_to_modify
                    for modifier in self.modifiers)
                self.modifier_vertices.update_size()
                for self_vert, vert in izip(
                    self.modifier_vertices,
                    chain(*(modifier.modifier_vertices
                            for modifier in self.modifiers))):
                    self_vert.x = vert.x
                    self_vert.y = vert.y
                    self_vert.z = vert.z
            else:
                self.num_modifier_vertices = 0
                self.modifier_vertices.update_size()
            # write the data
            pyffi.object_models.xml.struct_.StructBase.write(
                self, stream, self)

        def add_morph(self, name=None, relative_vertices=None):
            """Add a morph."""
            self.num_morphs += 1
            self.morphs.update_size()
            return self.morphs[-1]

        def add_modifier(self, name=None, relative_vertices=None):
            """Add a modifier."""
            self.num_modifiers += 1
            self.modifiers.update_size()
            return self.modifiers[-1]

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return ([morph for morph in self.morphs]
                    + [morph for morph in self.modifiers])

    # XXX copied from pyffi.formats.egm.EgmFormat.MorphRecord
    class MorphRecord:
        """
        >>> # create morph with 3 vertices.
        >>> morph = TriFormat.MorphRecord(argument=3)
        >>> morph.set_relative_vertices(
        ...     [(3, 5, 2), (1, 3, 2), (-9, 3, -1)])
        >>> # scale should be 9/32768.0 = 0.0002746...
        >>> morph.scale # doctest: +ELLIPSIS
        0.0002746...
        >>> for vert in morph.get_relative_vertices():
        ...     print([int(1000 * x + 0.5) for x in vert])
        [3000, 5000, 2000]
        [1000, 3000, 2000]
        [-8999, 3000, -999]
        """
        def get_relative_vertices(self):
            for vert in self.vertices:
                yield (vert.x * self.scale,
                       vert.y * self.scale,
                       vert.z * self.scale)

        def set_relative_vertices(self, vertices):
            # copy to list
            vertices = list(vertices)
            # check length
            if len(vertices) != self.arg:
                raise ValueError("expected %i vertices, but got %i"
                                 % (self.arg, len(vertices)))
            # get extreme values of morph
            max_value = max(max(abs(value) for value in vert)
                            for vert in vertices)
            # calculate scale
            self.scale = max_value / 32767.0
            inv_scale = 1 / self.scale
            # set vertices
            for vert, self_vert in izip(vertices, self.vertices):
                self_vert.x = int(vert[0] * inv_scale)
                self_vert.y = int(vert[1] * inv_scale)
                self_vert.z = int(vert[2] * inv_scale)

        def apply_scale(self, scale):
            """Apply scale factor to data.

            >>> # create morph with 3 vertices.
            >>> morph = TriFormat.MorphRecord(argument=3)
            >>> morph.set_relative_vertices(
            ...     [(3, 5, 2), (1, 3, 2), (-9, 3, -1)])
            >>> morph.apply_scale(2)
            >>> for vert in morph.get_relative_vertices():
            ...     print([int(1000 * x + 0.5) for x in vert])
            [6000, 10000, 4000]
            [2000, 6000, 4000]
            [-17999, 6000, -1999]
            """
            self.scale *= scale

if __name__=='__main__':
    import doctest
    doctest.testmod()
