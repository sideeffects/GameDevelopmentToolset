"""
:mod:`pyffi.formats.rockstar.dir_` --- DIR (.dir)
=================================================

A .dir file simply contains a list of files.

Implementation
--------------

.. autoclass:: DirFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a DIR file
^^^^^^^^^^^^^^^

>>> # check and read dir file
>>> stream = open('tests/rockstar/dir/test.dir', 'rb')
>>> data = DirFormat.Data()
>>> data.inspect(stream)
>>> # do some stuff with header?
>>> # XXX nothing for now
>>> # read directory
>>> data.read(stream)
>>> len(data.files)
2
>>> data.files[0].offset
0
>>> data.files[0].size
1
>>> data.files[0].name
'hello.txt'

Parse all DIR files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in DirFormat.walkData('tests/rockstar/dir'):
...     print(stream.name)
tests/rockstar/dir/test.dir

Create an DIR file from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> data = DirFormat.Data()
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data.write(stream)
"""

# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, Python File Format Interface
# All rights reserved.
#
# Redisdirbution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redisdirbutions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redisdirbutions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the disdirbution.
#
#    * Neither the name of the Python File Format Interface
#      project nor the names of its condirbutors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONDIRBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONDIRBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, SDIRCT
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

class DirFormat(pyffi.object_models.xml.FileFormat):
    """This class implements the DIR format."""
    xml_file_name = 'dir.xml'
    # where to look for dir.xml
    xml_file_path = [os.path.dirname(__file__)]
    # file name regular expression match
    RE_FILENAME = re.compile(r'^.*\.dir$', re.IGNORECASE)

    # basic types
    UInt = pyffi.object_models.common.UInt
    class String(pyffi.object_models.common.FixedString):
        _len = 24

    class Data(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual dir data."""

        def __init__(self, folder=None):
            """Initialize empty file list, or take list of files from
            a folder.
            """
            self.files = []
            offset = 0
            if folder:
                for filename in sorted(os.listdir(folder)):
                    if not os.path.isfile(os.path.join(folder, filename)):
                        continue
                    fileinfo = os.stat(os.path.join(folder, filename))
                    file_record = DirFormat.File()
                    file_record.offset = offset
                    file_record.size = (fileinfo.st_size + 2047) // 2048
                    file_record.name = filename
                    self.files.append(file_record)
                    offset += file_record.size

        def inspect_quick(self, stream):
            """Quickly checks if stream contains DIR data, by looking at
            the first 36 bytes.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                off1, size1, file1 = struct.unpack(
                    "<II24s", stream.read(32))
                try:
                    off2, = struct.unpack(
                        "<I", stream.read(4))
                except struct.error:
                    # this happens if .dir only contains one file record
                    off2 = size1
                if not(off1 == 0
                       #and size1 < 1000 # heuristic
                       and off2 == size1
                       and file1[-1] == '\x00'):
                    raise ValueError('Not a Rockstar DIR file.')
            finally:
                stream.seek(pos)

        # overriding pyffi.object_models.FileFormat.Data methods

        def inspect(self, stream):
            """Quickly checks if stream contains DIR data.

            :param stream: The stream to inspect.
            :type stream: file
            """
            pos = stream.tell()
            try:
                self.inspect_quick(stream)
            finally:
                stream.seek(pos)


        def read(self, stream):
            """Read a dir file.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            self.inspect_quick(stream)
            self.files = []
            pos = stream.tell()
            while stream.read(1):
                stream.seek(pos)
                file_record = DirFormat.File()
                file_record.read(stream, self)
                self.files.append(file_record)
                pos = stream.tell()

        def write(self, stream):
            """Write a dir file.

            :param stream: The stream to which to write.
            :type stream: ``file``
            """
            for file_record in self.files:
                file_record.write(stream, self)

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return self.files

        def unpack(self, image, folder):
            """Unpack all files, whose data resides in the given
            image, into the given folder.
            """
            for file_record in self.files:
                image.seek(file_record.offset * 2048)
                with open(os.path.join(folder, file_record.name), 'wb') as data:
                    data.write(image.read(file_record.size * 2048))

        def pack(self, image, folder):
            """Pack all files, whose data resides in the given folder,
            into the given image.
            """
            for file_record in self.files:
                if image.tell() != file_record.offset * 2048:
                    raise ValueError('file offset mismatch')
                with open(os.path.join(folder, file_record.name), 'rb') as data:
                    allbytes = data.read()
                    size = file_record.size * 2048
                    if len(allbytes) > size:
                        raise ValueError('file larger than record size')
                    image.write(allbytes)
                    if len(allbytes) < size:
                        image.write('\x00' * (size - len(allbytes)))

if __name__=='__main__':
    import doctest
    doctest.testmod()
