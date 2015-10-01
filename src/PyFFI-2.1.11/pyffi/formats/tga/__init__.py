"""
:mod:`pyffi.formats.tga` --- Targa (.tga)
=========================================

Implementation
--------------

.. autoclass:: TgaFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a TGA file
^^^^^^^^^^^^^^^

>>> # check and read tga file
>>> stream = open('tests/tga/test.tga', 'rb')
>>> data = TgaFormat.Data()
>>> data.inspect(stream)
>>> data.read(stream)
>>> stream.close()
>>> data.header.width
60
>>> data.header.height
20

Parse all TGA files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in TgaFormat.walkData('tests/tga'):
...     data.read(stream)
...     print(stream.name)
tests/tga/test.tga
tests/tga/test_footer.tga

Create a TGA file from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = TgaFormat.Data()
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data.write(stream)
>>> stream.close()
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

import struct, os, re

import pyffi.object_models.xml
import pyffi.object_models.common
import pyffi.object_models.xml.basic
import pyffi.object_models.xml.struct_
import pyffi.object_models
import pyffi.utils.graph
from pyffi.utils.graph import EdgeFilter

class TgaFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the TGA format."""
    xml_file_name = 'tga.xml'
    # where to look for tga.xml and in what order:
    # TGAXMLPATH env var, or TgaFormat module directory
    xml_file_path = [os.getenv('TGAXMLPATH'), os.path.dirname(__file__)]
    # filter for recognizing tga files by extension
    RE_FILENAME = re.compile(r'^.*\.tga$', re.IGNORECASE)

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.Byte
    ubyte = pyffi.object_models.common.UByte
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float
    PixelData = pyffi.object_models.common.UndecodedData

    class FooterString(pyffi.object_models.xml.basic.BasicBase):
        """The Targa footer signature."""
        def __str__(self):
            return 'TRUEVISION-XFILE.\x00'

        def read(self, stream, data):
            """Read signature from stream.

            :param stream: The stream to read from.
            :type stream: file
            """
            signat = stream.read(18)
            if signat != self.__str__().encode("ascii"):
                raise ValueError(
                    "invalid Targa signature: expected '%s' but got '%s'"
                    %(self.__str__(), signat))

        def write(self, stream, data):
            """Write signature to stream.

            :param stream: The stream to read from.
            :type stream: file
            """
            stream.write(self.__str__().encode("ascii"))

        def get_value(self):
            """Get signature.

            :return: The signature.
            """
            return self.__str__()

        def set_value(self, value):
            """Set signature.

            :param value: The value to assign.
            :type value: str
            """
            if value != self.__str__():
                raise ValueError(
                    "invalid Targa signature: expected '%s' but got '%s'"
                    %(self.__str__(), value))

        def get_size(self, data=None):
            """Return number of bytes that the signature occupies in a file.

            :return: Number of bytes.
            """
            return 18

        def get_hash(self, data=None):
            """Return a hash value for the signature.

            :return: An immutable object that can be used as a hash.
            """
            return self.__str__()

    class Image(pyffi.utils.graph.GlobalNode):
        def __init__(self):
            # children are either individual pixels, or RLE packets
            self.children = []

        def read(self, stream, data):
            data = data
            if data.header.image_type in (TgaFormat.ImageType.INDEXED,
                                          TgaFormat.ImageType.RGB,
                                          TgaFormat.ImageType.GREY):
                self.children = [
                    TgaFormat.Pixel(argument=data.header.pixel_size)
                    for i in xrange(data.header.width
                                    * data.header.height)]
                for pixel in self.children:
                    pixel.read(stream, data)
            else:
                self.children = []
                count = 0
                while count < data.header.width * data.header.height:
                    pixel = TgaFormat.RLEPixels(
                        argument=data.header.pixel_size)
                    pixel.read(stream, data)
                    self.children.append(pixel)
                    count += pixel.header.count + 1

        def write(self, stream, data):
            data = data
            for child in self.children:
                child.arg = data.header.pixel_size
                child.write(stream, data)

        def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
            for child in self.children:
                yield child

        def get_detail_child_names(self, edge_filter=EdgeFilter()):
            for i in xrange(len(self.children)):
                yield str(i)

    class Data(pyffi.object_models.FileFormat.Data):

        def __init__(self):
            self.header = TgaFormat.Header()
            self.image = TgaFormat.Image()
            self.footer = None # TgaFormat.Footer() is optional

        def inspect(self, stream):
            """Quick heuristic check if stream contains Targa data,
            by looking at the first 18 bytes.

            :param stream: The stream to inspect.
            :type stream: file
            """
            # XXX todo: set some of the actual fields of the header

            pos = stream.tell()
            # read header
            try:
                id_length, colormap_type, image_type, \
                colormap_index, colormap_length, colormap_size, \
                x_origin, y_origin, width, height, \
                pixel_size, flags = struct.unpack("<BBBHHBHHHHBB",
                                                  stream.read(18))
            except struct.error:
                # could not read 18 bytes
                # not a TGA file
                raise ValueError("Not a Targa file.")
            finally:
                stream.seek(pos)
            # check if tga type is valid
            # check pixel size
            # check width and height
            if not(image_type in (1, 2, 3, 9, 10, 11)
                   and pixel_size in (8, 24, 32)
                   and width <= 100000
                   and height <= 100000):
                raise ValueError("Not a Targa file.")
            # this looks like a tga file!

        def read(self, stream):
            """Read a tga file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            # read the file
            self.inspect(stream) # quick check

            # header
            self.header.read(stream, self)

            # image
            self.image.read(stream, self)
            
            # check if we are at the end of the file
            if not stream.read(1):
                self.footer = None
                return

            # footer
            stream.seek(-26, os.SEEK_END)
            self.footer = TgaFormat.Footer()
            self.footer.read(stream, self)

        def write(self, stream):
            """Write a tga file.

            :param stream: The stream to write to.
            :type stream: ``file``
            """
            self.header.write(stream, self)
            self.image.write(stream, self)
            if self.footer:
                self.footer.write(stream, self)

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            yield self.header
            yield self.image
            if self.footer:
                yield self.footer

        def get_global_child_names(self, edge_filter=EdgeFilter()):
            yield "Header"
            yield "Image"
            if self.footer:
                yield "Footer"

if __name__ == '__main__':
    import doctest
    doctest.testmod()
