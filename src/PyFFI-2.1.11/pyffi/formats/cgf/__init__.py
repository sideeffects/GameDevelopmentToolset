"""
:mod:`pyffi.formats.cgf` --- Crytek (.cgf and .cga)
===================================================

Implementation
--------------

.. autoclass:: CgfFormat
   :show-inheritance:
   :members:

Regression tests
----------------

Read a CGF file
^^^^^^^^^^^^^^^

>>> # get file version and file type, and read cgf file
>>> stream = open('tests/cgf/test.cgf', 'rb')
>>> data = CgfFormat.Data()
>>> # read chunk table only
>>> data.inspect(stream)
>>> # check chunk types
>>> list(chunktype.__name__ for chunktype in data.chunk_table.get_chunk_types())
['SourceInfoChunk', 'TimingChunk']
>>> data.chunks # no chunks yet
[]
>>> # read full file
>>> data.read(stream)
>>> # get all chunks
>>> for chunk in data.chunks:
...     print(chunk) # doctest: +ELLIPSIS
<class 'pyffi.formats.cgf.SourceInfoChunk'> instance at ...
* source_file : <None>
* date : Fri Sep 28 22:40:44 2007
* author : blender@BLENDER
<BLANKLINE>
<class 'pyffi.formats.cgf.TimingChunk'> instance at ...
* secs_per_tick : 0.000208333338378
* ticks_per_frame : 160
* global_range :
    <class 'pyffi.formats.cgf.RangeEntity'> instance at ...
    * name : GlobalRange
    * start : 0
    * end : 100
* num_sub_ranges : 0
<BLANKLINE>

Parse all CGF files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in CgfFormat.walkData('tests/cgf'):
...     print(stream.name)
...     try:
...         data.read(stream)
...     except Exception:
...         print("Warning: read failed due corrupt file, corrupt format description, or bug.")
...     print(len(data.chunks))
...     # do something with the chunks
...     for chunk in data.chunks:
...         chunk.apply_scale(2.0)
tests/cgf/invalid.cgf
Warning: read failed due corrupt file, corrupt format description, or bug.
0
tests/cgf/monkey.cgf
14
tests/cgf/test.cgf
2
tests/cgf/vcols.cgf
6

Create a CGF file from scratch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> from pyffi.formats.cgf import CgfFormat
>>> node1 = CgfFormat.NodeChunk()
>>> node1.name = "hello"
>>> node2 = CgfFormat.NodeChunk()
>>> node1.num_children = 1
>>> node1.children.update_size()
>>> node1.children[0] = node2
>>> node2.name = "world"
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> data = CgfFormat.Data() # default is far cry
>>> data.chunks = [node1, node2]
>>> # note: write returns number of padding bytes
>>> data.write(stream)
0
>>> # py3k returns 0 on seek; this hack removes return code from doctest
>>> if stream.seek(0): pass
>>> data.inspect_version_only(stream)
>>> hex(data.header.version)
'0x744'
>>> data.read(stream)
>>> # get all chunks
>>> for chunk in data.chunks:
...     print(chunk) # doctest: +ELLIPSIS +REPORT_NDIFF
<class 'pyffi.formats.cgf.NodeChunk'> instance at 0x...
* name : hello
* object : None
* parent : None
* num_children : 1
* material : None
* is_group_head : False
* is_group_member : False
* reserved_1 :
    <class 'pyffi.object_models.xml.array.Array'> instance at 0x...
    0: 0
    1: 0
* transform :
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
* pos : [  0.000  0.000  0.000 ]
* rot :
    <class 'pyffi.formats.cgf.Quat'> instance at 0x...
    * x : 0.0
    * y : 0.0
    * z : 0.0
    * w : 0.0
* scl : [  0.000  0.000  0.000 ]
* pos_ctrl : None
* rot_ctrl : None
* scl_ctrl : None
* property_string : <None>
* children :
    <class 'pyffi.object_models.xml.array.Array'> instance at 0x...
    0: <class 'pyffi.formats.cgf.NodeChunk'> instance at 0x...
<BLANKLINE>
<class 'pyffi.formats.cgf.NodeChunk'> instance at 0x...
* name : world
* object : None
* parent : None
* num_children : 0
* material : None
* is_group_head : False
* is_group_member : False
* reserved_1 :
    <class 'pyffi.object_models.xml.array.Array'> instance at 0x...
    0: 0
    1: 0
* transform :
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
    [  0.000  0.000  0.000  0.000 ]
* pos : [  0.000  0.000  0.000 ]
* rot :
    <class 'pyffi.formats.cgf.Quat'> instance at 0x...
    * x : 0.0
    * y : 0.0
    * z : 0.0
    * w : 0.0
* scl : [  0.000  0.000  0.000 ]
* pos_ctrl : None
* rot_ctrl : None
* scl_ctrl : None
* property_string : <None>
* children : <class 'pyffi.object_models.xml.array.Array'> instance at 0x...
<BLANKLINE>
"""

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

import itertools
import logging
import struct
import os
import re
import warnings
from itertools import izip


import pyffi.object_models.common
import pyffi.object_models
import pyffi.object_models.xml
import pyffi.utils.mathutils
import pyffi.utils.tangentspace
from pyffi.object_models.xml.basic import BasicBase
from pyffi.utils.graph import EdgeFilter

class _MetaCgfFormat(pyffi.object_models.xml.MetaFileFormat):
    """Metaclass which constructs the chunk map during class creation."""
    def __init__(cls, name, bases, dct):
        super(_MetaCgfFormat, cls).__init__(name, bases, dct)
        
        # map chunk type integers to chunk type classes
        cls.CHUNK_MAP = dict(
            (getattr(cls.ChunkType, chunk_name),
             getattr(cls, '%sChunk' % chunk_name))
            for chunk_name in cls.ChunkType._enumkeys
            if chunk_name != "ANY")

class CgfFormat(pyffi.object_models.xml.FileFormat):
    """Stores all information about the cgf file format."""
    __metaclass__ = _MetaCgfFormat
    xml_file_name = 'cgf.xml'
    # where to look for cgf.xml and in what order: CGFXMLPATH env var,
    # or module directory
    xml_file_path = [os.getenv('CGFXMLPATH'), os.path.dirname(__file__)]
    EPSILON = 0.0001 # used for comparing floats
    # regular expression for file name extension matching on cgf files
    RE_FILENAME = re.compile(r'^.*\.(cgf|cga|chr|caf)$', re.IGNORECASE)

    # version and user version for far cry
    VER_FARCRY = 0x744
    UVER_FARCRY = 1

    # version and user version for crysis
    VER_CRYSIS = 0x744
    UVER_CRYSIS = 2

    # basic types
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.Byte
    ubyte = pyffi.object_models.common.UByte
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    char = pyffi.object_models.common.Char
    float = pyffi.object_models.common.Float
    bool = pyffi.object_models.common.Bool
    String = pyffi.object_models.common.ZString
    SizedString = pyffi.object_models.common.SizedString

     # implementation of cgf-specific basic types

    class String16(pyffi.object_models.common.FixedString):
        """String of fixed length 16."""
        _len = 16

    class String32(pyffi.object_models.common.FixedString):
        """String of fixed length 32."""
        _len = 32

    class String64(pyffi.object_models.common.FixedString):
        """String of fixed length 64."""
        _len = 64

    class String128(pyffi.object_models.common.FixedString):
        """String of fixed length 128."""
        _len = 128

    class String256(pyffi.object_models.common.FixedString):
        """String of fixed length 256."""
        _len = 256

    class FileSignature(BasicBase):
        """The CryTek file signature with which every
        cgf file starts."""
        def __init__(self, **kwargs):
            super(CgfFormat.FileSignature, self).__init__(**kwargs)

        def __str__(self):
            return 'XXXXXX'

        def _str(self, data):
            if data.game == "Aion":
                return 'NCAion'.encode("ascii")
            else:
                return 'CryTek'.encode("ascii")

        def read(self, stream, data):
            """Read signature from stream.

            :param stream: The stream to read from.
            :type stream: file
            """
            gamesig = self._str(data)
            signat = stream.read(8)
            if not signat.startswith(gamesig):
                raise ValueError(
                    "invalid CGF signature: expected %s but got %s"
                    % (gamesig, signat))

        def write(self, stream, data):
            """Write signature to stream.

            :param stream: The stream to read from.
            :type stream: file
            """
            stream.write(self._str(data).ljust(8, '\x00'.encode("ascii")))

        def get_value(self):
            """Get signature.

            :return: The signature.
            """
            return self.__str__()

        def set_value(self, value):
            """Not implemented."""
            raise NotImplementedError("Cannot set signature value.")

        def get_size(self, data=None):
            """Return number of bytes that the signature occupies in a file.

            :return: Number of bytes.
            """
            return 8

        def get_hash(self, data=None):
            """Return a hash value for the signature.

            :return: An immutable object that can be used as a hash.
            """
            return self.__str__()

    class Ref(BasicBase):
        """Reference to a chunk, up the hierarchy."""
        _is_template = True
        _has_links = True
        _has_refs = True
        def __init__(self, **kwargs):
            super(CgfFormat.Ref, self).__init__(**kwargs)
            self._template = kwargs.get('template', type(None))
            self._value = None

        def get_value(self):
            """Get chunk being referred to.

            :return: The chunk being referred to.
            """
            return self._value

        def set_value(self, value):
            """Set chunk reference.

            :param value: The value to assign.
            :type value: L{CgfFormat.Chunk}
            """
            if value == None:
                self._value = None
            else:
                if not isinstance(value, self._template):
                    raise TypeError(
                        'expected an instance of %s but got instance of %s'
                        %(self._template, value.__class__))
                self._value = value

        def read(self, stream, data):
            """Read chunk index.

            :param stream: The stream to read from.
            :type stream: file
            """
            self._value = None # fix_links will set this field
            block_index, = struct.unpack('<i', stream.read(4))
            data._link_stack.append(block_index)

        def write(self, stream, data):
            """Write chunk index.

            :param stream: The stream to write to.
            :type stream: file
            """
            if self._value is None:
                stream.write(struct.pack('<i', -1))
            else:
                stream.write(struct.pack(
                    '<i', data._block_index_dct[self._value]))

        def fix_links(self, data):
            """Resolve chunk index into a chunk.

            :keyword block_dct: Dictionary mapping block index to block.
            :type block_dct: dict
            """
            logger = logging.getLogger("pyffi.cgf.data")
            block_index = data._link_stack.pop(0)
            # case when there's no link
            if block_index == -1:
                self._value = None
                return
            # other case: look up the link and check the link type
            try:
                block = data._block_dct[block_index]
            except KeyError:
                # make this raise an exception when all reference errors
                # are sorted out
                logger.warn("invalid chunk reference (%i)" % block_index)
                self._value = None
                return
            if not isinstance(block, self._template):
                if block_index == 0:
                    # crysis often uses index 0 to refer to an invalid index
                    # so don't complain on this one
                    block = None
                else:
                    # make this raise an exception when all reference errors
                    # are sorted out
                    logger.warn("""\
expected instance of %s
but got instance of %s""" % (self._template, block.__class__))
            self._value = block

        def get_links(self, data=None):
            """Return the chunk reference.

            :return: Empty list if no reference, or single item list containing
                the reference.
            """
            if self._value != None:
                return [self._value]
            else:
                return []

        def get_refs(self, data=None):
            """Return the chunk reference.

            :return: Empty list if no reference, or single item list containing
                the reference.
            """
            if self._value != None:
                return [self._value]
            else:
                return []

        def __str__(self):
            # don't recurse
            if self._value != None:
                return '%s instance at 0x%08X'\
                       % (self._value.__class__, id(self._value))
            else:
                return 'None'

        def get_size(self, data=None):
            """Return number of bytes this type occupies in a file.

            :return: Number of bytes.
            """
            return 4

        def get_hash(self, data=None):
            """Return a hash value for the chunk referred to.

            :return: An immutable object that can be used as a hash.
            """
            return self._value.get_hash() if not self._value is None else None

    class Ptr(Ref):
        """Reference to a chunk, down the hierarchy."""
        _is_template = True
        _has_links = True
        _has_refs = False

        def __str__(self):
            # avoid infinite recursion
            if self._value != None:
                return '%s instance at 0x%08X'\
                       % (self._value.__class__, id(self._value))
            else:
                return 'None'

        def get_refs(self, data=None):
            """Ptr does not point down, so get_refs returns empty list.

            :return: C{[]}
            """
            return []

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.

        :param version_str: The version string.
        :type version_str: str
        :return: A version integer.

        >>> hex(CgfFormat.version_number('744'))
        '0x744'
        """
        return int(version_str, 16)

    # exceptions
    class CgfError(Exception):
        """Exception for CGF specific errors."""
        pass

    class Data(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual cgf data.

        Note that L{versions} and L{chunk_table} are not automatically kept
        in sync with the L{chunks}, but they are
        resynchronized when calling L{write}.

        :ivar game: The cgf game.
        :type game: ``int``
        :ivar header: The cgf header.
        :type header: L{CgfFormat.Header}
        :ivar chunks: List of chunks (the actual data).
        :type chunks: ``list`` of L{CgfFormat.Chunk}
        :ivar versions: List of chunk versions.
        :type versions: ``list`` of L{int}
        """
        _link_stack = None
        _block_index_dct = None
        _block_dct = None

        def __init__(self, filetype=0xffff0000, game="Far Cry"):
            # 0xffff0000 = CgfFormat.FileType.GEOM

            """Initialize cgf data. By default, this creates an empty
            cgf document of the given filetype and game.

            :param filetype: The file type (animation, or geometry).
            :type filetype: ``int``
            :param game: The game.
            :type game: ``str``
            """
            # create new header
            self.header = CgfFormat.Header()
            self.header.type = filetype
            self.header.version = 0x744 # no other chunk table versions
            # empty list of chunks
            self.chunks = []
            # empty list of versions (one per chunk)
            self.versions = []
            # chunk table
            self.chunk_table = CgfFormat.ChunkTable()
            # game
            # TODO store this in a way that can be displayed by qskope
            self.game = game
            # set version and user version
            self.version = self.header.version
            if self.game == "Far Cry":
                self.user_version = CgfFormat.UVER_FARCRY
            elif self.game == "Crysis":
                self.user_version = CgfFormat.UVER_CRYSIS
            elif self.game == "Aion":
                # XXX guessing for Aion!
                self.user_version = CgfFormat.UVER_FARCRY
            else:
                raise ValueError("unknown game %s" % game)

        # new functions

        def inspect_version_only(self, stream):
            """This function checks the version only, and is faster
            than the usual inspect function (which reads the full
            chunk table). Sets the L{header} and L{game} instance
            variables if the stream contains a valid cgf file.

            Call this function if you simply wish to check that a file is
            a cgf file without having to parse even the header.

            :raise ``ValueError``: If the stream does not contain a cgf file.
            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            pos = stream.tell()
            try:
                signat = stream.read(8)
                filetype, version, offset = struct.unpack('<III',
                                                          stream.read(12))
            except IOError:
                raise
            except Exception:
                # something went wrong with unpack
                # this means that the file is less than 20 bytes
                # cannot be a cgf file
                raise ValueError("File too small to be a cgf file.")
            finally:
                stream.seek(pos)

            # test the data
            if (signat[:6] != "CryTek".encode("ascii")
                and signat[:6] != "NCAion".encode("ascii")):
                raise ValueError(
                    "Invalid signature (got '%s' instead of 'CryTek' or 'NCAion')"
                    % signat[:6])
            if filetype not in (CgfFormat.FileType.GEOM,
                                CgfFormat.FileType.ANIM):
                raise ValueError("Invalid file type.")
            if version not in CgfFormat.versions.values():
                raise ValueError("Invalid file version.")
            # quick and lame game check:
            # far cry has chunk table at the end, crysis at the start
            if signat[:6] == "NCAion".encode("ascii"):
                self.game = "Aion"
            elif offset == 0x14:
                self.game = "Crysis"
            else:
                self.game = "Far Cry"
            # load the actual header
            try:
                self.header.read(stream, self)
            finally:
                stream.seek(pos)
            # set version and user version
            self.version = self.header.version
            if self.game == "Far Cry":
                self.user_version = CgfFormat.UVER_FARCRY
            elif self.game == "Crysis":
                self.user_version = CgfFormat.UVER_CRYSIS
            elif self.game == "Aion":
                # XXX guessing for Aion!
                self.user_version = CgfFormat.UVER_FARCRY
            else:
                raise ValueError("unknown game %s" % game)

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            """Returns chunks without parent."""
            # calculate all children of all chunks
            children = set()
            for chunk in self.chunks:
                children |= set(chunk.get_global_child_nodes())
            # iterate over all chunks that are NOT in the list of children
            return (chunk for chunk in self.chunks
                    if not chunk in children)

        # DetailNode

        def replace_global_node(self, oldbranch, newbranch,
                                edge_filter=EdgeFilter()):
            for i, chunk in enumerate(self.chunks):
                if chunk is oldbranch:
                    self.chunks[i] = newbranch
                else:
                    chunk.replace_global_node(oldbranch, newbranch,
                                            edge_filter=edge_filter)

        def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
            yield self.header
            yield self.chunk_table

        def get_detail_child_names(self, edge_filter=EdgeFilter()):
            yield "header"
            yield "chunk table"

        # overriding pyffi.object_models.FileFormat.Data methods

        def inspect(self, stream):
            """Quickly checks whether the stream appears to contain
            cgf data, and read the cgf header and chunk table. Resets stream to
            original position.

            Call this function if you only need to inspect the header and
            chunk table.

            :param stream: The file to inspect.
            :type stream: ``file``
            """
            logger = logging.getLogger("pyffi.cgf.data")
            pos = stream.tell()
            try:
                logger.debug("Reading header at 0x%08X." % stream.tell())
                self.inspect_version_only(stream)
                self.header.read(stream, data=self)
                stream.seek(self.header.offset)
                logger.debug("Reading chunk table version 0x%08X at 0x%08X." % (self.header.version, stream.tell()))
                self.chunk_table.read(stream, self)
            finally:
                stream.seek(pos)

        def read(self, stream):
            """Read a cgf file. Does not reset stream position.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            validate = True # whether we validate on reading
            
            logger = logging.getLogger("pyffi.cgf.data")
            self.inspect(stream)

            # is it a caf file? these are missing chunk headers on controllers
            # (note: stream.name may not be a python string for some file
            # implementations, notably PyQt4, so convert it explicitely)
            is_caf = (str(stream.name)[-4:].lower() == ".caf")

            chunk_types = [
                chunk_type for chunk_type in dir(CgfFormat.ChunkType) \
                if chunk_type[:2] != '__']

            # get the chunk sizes (for double checking that we have all data)
            if validate:
                chunk_offsets = [chunkhdr.offset
                                 for chunkhdr in self.chunk_table.chunk_headers]
                chunk_offsets.append(self.header.offset)
                chunk_sizes = []
                for chunkhdr in self.chunk_table.chunk_headers:
                    next_chunk_offsets = [offset for offset in chunk_offsets
                                          if offset > chunkhdr.offset]
                    if next_chunk_offsets:
                        chunk_sizes.append(min(next_chunk_offsets) - chunkhdr.offset)
                    else:
                        stream.seek(0, 2)
                        chunk_sizes.append(stream.tell() - chunkhdr.offset)

            # read the chunks
            self._link_stack = [] # list of chunk identifiers, as added to the stack
            self._block_dct = {} # maps chunk index to actual chunk
            self.chunks = [] # records all chunks as read from cgf file in proper order
            self.versions = [] # records all chunk versions as read from cgf file
            for chunknum, chunkhdr in enumerate(self.chunk_table.chunk_headers):
                # check that id is unique
                if chunkhdr.id in self._block_dct:
                    raise ValueError('chunk id %i not unique'%chunkhdr.id)

                # get chunk type
                for chunk_type in chunk_types:
                    if getattr(CgfFormat.ChunkType, chunk_type) == chunkhdr.type:
                        break
                else:
                    raise ValueError('unknown chunk type 0x%08X'%chunkhdr.type)
                try:
                    chunk = getattr(CgfFormat, '%sChunk' % chunk_type)()
                except AttributeError:
                    raise ValueError(
                        'undecoded chunk type 0x%08X (%sChunk)'
                        %(chunkhdr.type, chunk_type))
                # check the chunk version
                if not self.game in chunk.get_games():
                    logger.error(
                        'game %s does not support %sChunk; '
                        'trying anyway'
                        % (self.game, chunk_type))
                if not chunkhdr.version in chunk.get_versions(self.game):
                    logger.error(
                        'chunk version 0x%08X not supported for '
                        'game %s and %sChunk; '
                        'trying anyway'
                        % (chunkhdr.version, self.game, chunk_type))

                # now read the chunk
                stream.seek(chunkhdr.offset)
                logger.debug("Reading %s chunk version 0x%08X at 0x%08X"
                             % (chunk_type, chunkhdr.version, stream.tell()))

                # in far cry, most chunks start with a copy of chunkhdr
                # in crysis, more chunks start with chunkhdr
                # caf files are special: they don't have headers on controllers
                if not(self.user_version == CgfFormat.UVER_FARCRY
                       and chunkhdr.type in [
                           CgfFormat.ChunkType.SourceInfo,
                           CgfFormat.ChunkType.BoneNameList,
                           CgfFormat.ChunkType.BoneLightBinding,
                           CgfFormat.ChunkType.BoneInitialPos,
                           CgfFormat.ChunkType.MeshMorphTarget]) \
                    and not(self.user_version == CgfFormat.UVER_CRYSIS
                            and chunkhdr.type in [
                                CgfFormat.ChunkType.BoneNameList,
                                CgfFormat.ChunkType.BoneInitialPos]) \
                    and not(is_caf
                            and chunkhdr.type in [
                                CgfFormat.ChunkType.Controller]) \
                    and not((self.game == "Aion") and chunkhdr.type in [
                        CgfFormat.ChunkType.MeshPhysicsData,
                        CgfFormat.ChunkType.MtlName]):
                    chunkhdr_copy = CgfFormat.ChunkHeader()
                    chunkhdr_copy.read(stream, self)
                    # check that the copy is valid
                    # note: chunkhdr_copy.offset != chunkhdr.offset check removed
                    # as many crysis cgf files have this wrong
                    if chunkhdr_copy.type != chunkhdr.type \
                       or chunkhdr_copy.version != chunkhdr.version \
                       or chunkhdr_copy.id != chunkhdr.id:
                        raise ValueError(
                            'chunk starts with invalid header:\n\
expected\n%sbut got\n%s'%(chunkhdr, chunkhdr_copy))
                else:
                    chunkhdr_copy = None

                # quick hackish trick with version... not beautiful but it works
                self.version = chunkhdr.version
                try:
                    chunk.read(stream, self)
                finally:
                    self.version = self.header.version
                self.chunks.append(chunk)
                self.versions.append(chunkhdr.version)
                self._block_dct[chunkhdr.id] = chunk

                if validate:
                    # calculate size
                    # (quick hackish trick with version)
                    self.version = chunkhdr.version
                    try:
                        size = chunk.get_size(self)
                    finally:
                        self.version = self.header.version
                    # take into account header copy
                    if chunkhdr_copy:
                        size += chunkhdr_copy.get_size(self)
                    # check with number of bytes read
                    if size != stream.tell() - chunkhdr.offset:
                        logger.error("""\
get_size returns wrong size when reading %s at 0x%08X
actual bytes read is %i, get_size yields %i (expected %i bytes)"""
                                    % (chunk.__class__.__name__,
                                       chunkhdr.offset,
                                       size,
                                       stream.tell() - chunkhdr.offset,
                                       chunk_sizes[chunknum]))
                    # check for padding bytes
                    if chunk_sizes[chunknum] & 3 == 0:
                        padlen = ((4 - size & 3) & 3)
                        #assert(stream.read(padlen) == '\x00' * padlen)
                        size += padlen
                    # check size
                    if size != chunk_sizes[chunknum]:
                        logger.warn("""\
chunk size mismatch when reading %s at 0x%08X
%i bytes available, but actual bytes read is %i"""
                                    % (chunk.__class__.__name__,
                                       chunkhdr.offset,
                                       chunk_sizes[chunknum], size))

            # fix links
            for chunk, chunkversion in zip(self.chunks, self.versions):
                # (quick hackish trick with version)
                self.version = chunkversion
                try:
                    #print(chunk.__class__)
                    chunk.fix_links(self)
                finally:
                    self.version = self.header.version
            if self._link_stack != []:
                raise CgfFormat.CgfError(
                    'not all links have been popped from the stack (bug?)')

        def write(self, stream):
            """Write a cgf file. The L{header} and L{chunk_table} are
            recalculated from L{chunks}. Returns number of padding bytes
            written (this is for debugging purposes only).

            :param stream: The stream to which to write.
            :type stream: file
            :return: Number of padding bytes written.
            """
            logger = logging.getLogger("pyffi.cgf.data")
            # is it a caf file? these are missing chunk headers on controllers
            is_caf = (str(stream.name)[-4:].lower() == ".caf")

            # variable to track number of padding bytes
            total_padding = 0

            # chunk versions
            self.update_versions()

            # write header
            hdr_pos = stream.tell()
            self.header.offset = -1 # is set at the end
            self.header.write(stream, self)

            # chunk id is simply its index in the chunks list
            self._block_index_dct = dict(
                (chunk, i) for i, chunk in enumerate(self.chunks))

            # write chunks and add headers to chunk table
            self.chunk_table = CgfFormat.ChunkTable()
            self.chunk_table.num_chunks = len(self.chunks)
            self.chunk_table.chunk_headers.update_size()
            #print(self.chunk_table) # DEBUG

            # crysis: write chunk table now
            if self.user_version == CgfFormat.UVER_CRYSIS:
                self.header.offset = stream.tell()
                self.chunk_table.write(stream, self)

            for chunkhdr, chunk, chunkversion in zip(self.chunk_table.chunk_headers,
                                                     self.chunks, self.versions):
                logger.debug("Writing %s chunk version 0x%08X at 0x%08X" % (chunk.__class__.__name__, chunkhdr.version, stream.tell()))

                # set up chunk header
                chunkhdr.type = getattr(
                    CgfFormat.ChunkType, chunk.__class__.__name__[:-5])
                chunkhdr.version = chunkversion
                chunkhdr.offset = stream.tell()
                chunkhdr.id = self._block_index_dct[chunk]
                # write chunk header
                if not(self.user_version == CgfFormat.UVER_FARCRY
                       and chunkhdr.type in [
                           CgfFormat.ChunkType.SourceInfo,
                           CgfFormat.ChunkType.BoneNameList,
                           CgfFormat.ChunkType.BoneLightBinding,
                           CgfFormat.ChunkType.BoneInitialPos,
                           CgfFormat.ChunkType.MeshMorphTarget]) \
                    and not(self.user_version == CgfFormat.UVER_CRYSIS
                            and chunkhdr.type in [
                                CgfFormat.ChunkType.BoneNameList,
                                CgfFormat.ChunkType.BoneInitialPos]) \
                    and not(is_caf
                            and chunkhdr.type in [
                                CgfFormat.ChunkType.Controller]):
                    #print(chunkhdr) # DEBUG
                    chunkhdr.write(stream, self)
                # write chunk (with version hack)
                self.version = chunkversion
                try:
                    chunk.write(stream, self)
                finally:
                    self.version = self.header.version
                # write padding bytes to align blocks
                padlen = (4 - stream.tell() & 3) & 3
                if padlen:
                    stream.write("\x00".encode("ascii") * padlen)
                    total_padding += padlen

            # write/update chunk table
            logger.debug("Writing chunk table version 0x%08X at 0x%08X"
                         % (self.header.version, stream.tell()))
            if self.user_version == CgfFormat.UVER_CRYSIS:
                end_pos = stream.tell()
                stream.seek(self.header.offset)
                self.chunk_table.write(stream, self)
            else:
                self.header.offset = stream.tell()
                self.chunk_table.write(stream, self)
                end_pos = stream.tell()

            # update header
            stream.seek(hdr_pos)
            self.header.write(stream, self)

            # seek end of written data
            stream.seek(end_pos)

            # return number of padding bytes written
            return total_padding

        def update_versions(self):
            """Update L{versions} for the given chunks and game."""
            try:
                self.versions = [max(chunk.get_versions(self.game))
                                 for chunk in self.chunks]
            except KeyError:
                raise CgfFormat.CgfError("game %s not supported" % self.game)

    # extensions of generated structures

    class Chunk:
        def tree(self, block_type = None, follow_all = True):
            """A generator for parsing all blocks in the tree (starting from and
            including C{self}).

            :param block_type: If not ``None``, yield only blocks of the type C{block_type}.
            :param follow_all: If C{block_type} is not ``None``, then if this is ``True`` the function will parse the whole tree. Otherwise, the function will not follow branches that start by a non-C{block_type} block."""
            # yield self
            if not block_type:
                yield self
            elif isinstance(self, block_type):
                yield self
            elif not follow_all:
                return # don't recurse further

            # yield tree attached to each child
            for child in self.get_refs():
                for block in child.tree(block_type = block_type, follow_all = follow_all):
                    yield block

        def apply_scale(self, scale):
            """Apply scale factor on data."""
            pass

    class ChunkTable:
        def get_chunk_types(self):
            """Iterate all chunk types (in the form of Python classes) referenced
            in this table.
            """
            return (CgfFormat.CHUNK_MAP[chunk_header.type]
                    for chunk_header in self.chunk_headers)

    class BoneInitialPosChunk:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            for mat in self.initial_pos_matrices:
                mat.pos.x *= scale
                mat.pos.y *= scale
                mat.pos.z *= scale

        def get_global_node_parent(self):
            """Get the block parent (used for instance in the QSkope global
            view)."""
            return self.mesh

    class DataStreamChunk:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            for vert in self.vertices:
                vert.x *= scale
                vert.y *= scale
                vert.z *= scale

    class Matrix33:
        def as_list(self):
            """Return matrix as 3x3 list."""
            return [
                [self.m_11, self.m_12, self.m_13],
                [self.m_21, self.m_22, self.m_23],
                [self.m_31, self.m_32, self.m_33]
                ]

        def as_tuple(self):
            """Return matrix as 3x3 tuple."""
            return (
                (self.m_11, self.m_12, self.m_13),
                (self.m_21, self.m_22, self.m_23),
                (self.m_31, self.m_32, self.m_33)
                )

        def __str__(self):
            return(
                "[ %6.3f %6.3f %6.3f ]\n[ %6.3f %6.3f %6.3f ]\n[ %6.3f %6.3f %6.3f ]\n"
                % (self.m_11, self.m_12, self.m_13,
                   self.m_21, self.m_22, self.m_23,
                   self.m_31, self.m_32, self.m_33))

        def set_identity(self):
            """Set to identity matrix."""
            self.m_11 = 1.0
            self.m_12 = 0.0
            self.m_13 = 0.0
            self.m_21 = 0.0
            self.m_22 = 1.0
            self.m_23 = 0.0
            self.m_31 = 0.0
            self.m_32 = 0.0
            self.m_33 = 1.0

        def is_identity(self):
            """Return ``True`` if the matrix is close to identity."""
            if  (abs(self.m_11 - 1.0) > CgfFormat.EPSILON
                 or abs(self.m_12) > CgfFormat.EPSILON
                 or abs(self.m_13) > CgfFormat.EPSILON
                 or abs(self.m_21) > CgfFormat.EPSILON
                 or abs(self.m_22 - 1.0) > CgfFormat.EPSILON
                 or abs(self.m_23) > CgfFormat.EPSILON
                 or abs(self.m_31) > CgfFormat.EPSILON
                 or abs(self.m_32) > CgfFormat.EPSILON
                 or abs(self.m_33 - 1.0) > CgfFormat.EPSILON):
                return False
            else:
                return True

        def get_copy(self):
            """Return a copy of the matrix."""
            mat = CgfFormat.Matrix33()
            mat.m_11 = self.m_11
            mat.m_12 = self.m_12
            mat.m_13 = self.m_13
            mat.m_21 = self.m_21
            mat.m_22 = self.m_22
            mat.m_23 = self.m_23
            mat.m_31 = self.m_31
            mat.m_32 = self.m_32
            mat.m_33 = self.m_33
            return mat

        def get_transpose(self):
            """Get transposed of the matrix."""
            mat = CgfFormat.Matrix33()
            mat.m_11 = self.m_11
            mat.m_12 = self.m_21
            mat.m_13 = self.m_31
            mat.m_21 = self.m_12
            mat.m_22 = self.m_22
            mat.m_23 = self.m_32
            mat.m_31 = self.m_13
            mat.m_32 = self.m_23
            mat.m_33 = self.m_33
            return mat

        def is_scale_rotation(self):
            """Returns true if the matrix decomposes nicely into scale * rotation."""
            # NOTE: 0.01 instead of CgfFormat.EPSILON to work around bad files

            # calculate self * self^T
            # this should correspond to
            # (scale * rotation) * (scale * rotation)^T
            # = scale * rotation * rotation^T * scale^T
            # = scale * scale^T
            self_transpose = self.get_transpose()
            mat = self * self_transpose

            # off diagonal elements should be zero
            if (abs(mat.m_12) + abs(mat.m_13)
                + abs(mat.m_21) + abs(mat.m_23)
                + abs(mat.m_31) + abs(mat.m_32)) > 0.01:
                return False

            return True

        def is_rotation(self):
            """Returns ``True`` if the matrix is a rotation matrix
            (a member of SO(3))."""
            # NOTE: 0.01 instead of CgfFormat.EPSILON to work around bad files

            if not self.is_scale_rotation():
                return False
            scale = self.get_scale()
            if abs(scale.x - 1.0) > 0.01 \
               or abs(scale.y - 1.0) > 0.01 \
               or abs(scale.z - 1.0) > 0.01:
                return False
            return True

        def get_determinant(self):
            """Return determinant."""
            return (self.m_11*self.m_22*self.m_33
                    +self.m_12*self.m_23*self.m_31
                    +self.m_13*self.m_21*self.m_32
                    -self.m_31*self.m_22*self.m_13
                    -self.m_21*self.m_12*self.m_33
                    -self.m_11*self.m_32*self.m_23)

        def get_scale(self):
            """Gets the scale (assuming is_scale_rotation is true!)."""
            # calculate self * self^T
            # this should correspond to
            # (rotation * scale)* (rotation * scale)^T
            # = scale * scale^T
            # = diagonal matrix with scales squared on the diagonal
            mat = self * self.get_transpose()

            scale = CgfFormat.Vector3()
            scale.x = mat.m_11 ** 0.5
            scale.y = mat.m_22 ** 0.5
            scale.z = mat.m_33 ** 0.5

            if self.get_determinant() < 0:
                return -scale
            else:
                return scale

        def get_scale_rotation(self):
            """Decompose the matrix into scale and rotation, where scale is a float
            and rotation is a C{Matrix33}. Returns a pair (scale, rotation)."""
            rot = self.get_copy()
            scale = self.get_scale()
            if min(abs(x) for x in scale.as_tuple()) < CgfFormat.EPSILON:
                raise ZeroDivisionError('scale is zero, unable to obtain rotation')
            rot.m_11 /= scale.x
            rot.m_12 /= scale.x
            rot.m_13 /= scale.x
            rot.m_21 /= scale.y
            rot.m_22 /= scale.y
            rot.m_23 /= scale.y
            rot.m_31 /= scale.z
            rot.m_32 /= scale.z
            rot.m_33 /= scale.z
            return (scale, rot)

        def set_scale_rotation(self, scale, rotation):
            """Compose the matrix as the product of scale * rotation."""
            if not isinstance(scale, CgfFormat.Vector3):
                raise TypeError('scale must be Vector3')
            if not isinstance(rotation, CgfFormat.Matrix33):
                raise TypeError('rotation must be Matrix33')

            if not rotation.is_rotation():
                raise ValueError('rotation must be rotation matrix')

            self.m_11 = rotation.m_11 * scale.x
            self.m_12 = rotation.m_12 * scale.x
            self.m_13 = rotation.m_13 * scale.x
            self.m_21 = rotation.m_21 * scale.y
            self.m_22 = rotation.m_22 * scale.y
            self.m_23 = rotation.m_23 * scale.y
            self.m_31 = rotation.m_31 * scale.z
            self.m_32 = rotation.m_32 * scale.z
            self.m_33 = rotation.m_33 * scale.z

        def get_scale_quat(self):
            """Decompose matrix into scale and quaternion."""
            scale, rot = self.get_scale_rotation()
            quat = CgfFormat.Quat()
            trace = 1.0 + rot.m_11 + rot.m_22 + rot.m_33

            if trace > CgfFormat.EPSILON:
                s = (trace ** 0.5) * 2
                quat.x = -( rot.m_32 - rot.m_23 ) / s
                quat.y = -( rot.m_13 - rot.m_31 ) / s
                quat.z = -( rot.m_21 - rot.m_12 ) / s
                quat.w = 0.25 * s
            elif rot.m_11 > max((rot.m_22, rot.m_33)):
                s  = (( 1.0 + rot.m_11 - rot.m_22 - rot.m_33 ) ** 0.5) * 2
                quat.x = 0.25 * s
                quat.y = (rot.m_21 + rot.m_12 ) / s
                quat.z = (rot.m_13 + rot.m_31 ) / s
                quat.w = -(rot.m_32 - rot.m_23 ) / s
            elif rot.m_22 > rot.m_33:
                s  = (( 1.0 + rot.m_22 - rot.m_11 - rot.m_33 ) ** 0.5) * 2
                quat.x = (rot.m_21 + rot.m_12 ) / s
                quat.y = 0.25 * s
                quat.z = (rot.m_32 + rot.m_23 ) / s
                quat.w = -(rot.m_13 - rot.m_31 ) / s
            else:
                s  = (( 1.0 + rot.m_33 - rot.m_11 - rot.m_22 ) ** 0.5) * 2
                quat.x = (rot.m_13 + rot.m_31 ) / s
                quat.y = (rot.m_32 + rot.m_23 ) / s
                quat.z = 0.25 * s
                quat.w = -(rot.m_21 - rot.m_12 ) / s

            return scale, quat


        def get_inverse(self):
            """Get inverse (assuming is_scale_rotation is true!)."""
            # transpose inverts rotation but keeps the scale
            # dividing by scale^2 inverts the scale as well
            scale = self.get_scale()
            mat = self.get_transpose()
            mat.m_11 /= scale.x ** 2
            mat.m_12 /= scale.x ** 2
            mat.m_13 /= scale.x ** 2
            mat.m_21 /= scale.y ** 2
            mat.m_22 /= scale.y ** 2
            mat.m_23 /= scale.y ** 2
            mat.m_31 /= scale.z ** 2
            mat.m_32 /= scale.z ** 2
            mat.m_33 /= scale.z ** 2

        def __mul__(self, rhs):
            if isinstance(rhs, (float, int, long)):
                mat = CgfFormat.Matrix33()
                mat.m_11 = self.m_11 * rhs
                mat.m_12 = self.m_12 * rhs
                mat.m_13 = self.m_13 * rhs
                mat.m_21 = self.m_21 * rhs
                mat.m_22 = self.m_22 * rhs
                mat.m_23 = self.m_23 * rhs
                mat.m_31 = self.m_31 * rhs
                mat.m_32 = self.m_32 * rhs
                mat.m_33 = self.m_33 * rhs
                return mat
            elif isinstance(rhs, CgfFormat.Vector3):
                raise TypeError("matrix*vector not supported;\
        please use left multiplication (vector*matrix)")
            elif isinstance(rhs, CgfFormat.Matrix33):
                mat = CgfFormat.Matrix33()
                mat.m_11 = self.m_11 * rhs.m_11 + self.m_12 * rhs.m_21 + self.m_13 * rhs.m_31
                mat.m_12 = self.m_11 * rhs.m_12 + self.m_12 * rhs.m_22 + self.m_13 * rhs.m_32
                mat.m_13 = self.m_11 * rhs.m_13 + self.m_12 * rhs.m_23 + self.m_13 * rhs.m_33
                mat.m_21 = self.m_21 * rhs.m_11 + self.m_22 * rhs.m_21 + self.m_23 * rhs.m_31
                mat.m_22 = self.m_21 * rhs.m_12 + self.m_22 * rhs.m_22 + self.m_23 * rhs.m_32
                mat.m_23 = self.m_21 * rhs.m_13 + self.m_22 * rhs.m_23 + self.m_23 * rhs.m_33
                mat.m_31 = self.m_31 * rhs.m_11 + self.m_32 * rhs.m_21 + self.m_33 * rhs.m_31
                mat.m_32 = self.m_31 * rhs.m_12 + self.m_32 * rhs.m_22 + self.m_33 * rhs.m_32
                mat.m_33 = self.m_31 * rhs.m_13 + self.m_32 * rhs.m_23 + self.m_33 * rhs.m_33
                return mat
            else:
                raise TypeError(
                    "do not know how to multiply Matrix33 with %s"%rhs.__class__)

        def __div__(self, rhs):
            if isinstance(rhs, (float, int, long)):
                mat = CgfFormat.Matrix33()
                mat.m_11 = self.m_11 / rhs
                mat.m_12 = self.m_12 / rhs
                mat.m_13 = self.m_13 / rhs
                mat.m_21 = self.m_21 / rhs
                mat.m_22 = self.m_22 / rhs
                mat.m_23 = self.m_23 / rhs
                mat.m_31 = self.m_31 / rhs
                mat.m_32 = self.m_32 / rhs
                mat.m_33 = self.m_33 / rhs
                return mat
            else:
                raise TypeError(
                    "do not know how to divide Matrix33 by %s"%rhs.__class__)

        def __rmul__(self, lhs):
            if isinstance(lhs, (float, int, long)):
                return self * lhs # commutes
            else:
                raise TypeError(
                    "do not know how to multiply %s with Matrix33"%lhs.__class__)

        def __eq__(self, mat):
            if not isinstance(mat, CgfFormat.Matrix33):
                raise TypeError(
                    "do not know how to compare Matrix33 and %s"%mat.__class__)
            if (abs(self.m_11 - mat.m_11) > CgfFormat.EPSILON
                or abs(self.m_12 - mat.m_12) > CgfFormat.EPSILON
                or abs(self.m_13 - mat.m_13) > CgfFormat.EPSILON
                or abs(self.m_21 - mat.m_21) > CgfFormat.EPSILON
                or abs(self.m_22 - mat.m_22) > CgfFormat.EPSILON
                or abs(self.m_23 - mat.m_23) > CgfFormat.EPSILON
                or abs(self.m_31 - mat.m_31) > CgfFormat.EPSILON
                or abs(self.m_32 - mat.m_32) > CgfFormat.EPSILON
                or abs(self.m_33 - mat.m_33) > CgfFormat.EPSILON):
                return False
            return True

        def __ne__(self, mat):
            return not self.__eq__(mat)

    class Matrix44:
        def as_list(self):
            """Return matrix as 4x4 list."""
            return [
                [self.m_11, self.m_12, self.m_13, self.m_14],
                [self.m_21, self.m_22, self.m_23, self.m_24],
                [self.m_31, self.m_32, self.m_33, self.m_34],
                [self.m_41, self.m_42, self.m_43, self.m_44]
                ]

        def as_tuple(self):
            """Return matrix as 4x4 tuple."""
            return (
                (self.m_11, self.m_12, self.m_13, self.m_14),
                (self.m_21, self.m_22, self.m_23, self.m_24),
                (self.m_31, self.m_32, self.m_33, self.m_34),
                (self.m_41, self.m_42, self.m_43, self.m_44)
                )

        def set_rows(self, row0, row1, row2, row3):
            """Set matrix from rows."""
            self.m_11, self.m_12, self.m_13, self.m_14 = row0
            self.m_21, self.m_22, self.m_23, self.m_24 = row1
            self.m_31, self.m_32, self.m_33, self.m_34 = row2
            self.m_41, self.m_42, self.m_43, self.m_44 = row3

        def __str__(self):
            return(
                '[ %6.3f %6.3f %6.3f %6.3f ]\n'
                '[ %6.3f %6.3f %6.3f %6.3f ]\n'
                '[ %6.3f %6.3f %6.3f %6.3f ]\n'
                '[ %6.3f %6.3f %6.3f %6.3f ]\n'
                % (self.m_11, self.m_12, self.m_13, self.m_14,
                   self.m_21, self.m_22, self.m_23, self.m_24,
                   self.m_31, self.m_32, self.m_33, self.m_34,
                   self.m_41, self.m_42, self.m_43, self.m_44))

        def set_identity(self):
            """Set to identity matrix."""
            self.m_11 = 1.0
            self.m_12 = 0.0
            self.m_13 = 0.0
            self.m_14 = 0.0
            self.m_21 = 0.0
            self.m_22 = 1.0
            self.m_23 = 0.0
            self.m_24 = 0.0
            self.m_31 = 0.0
            self.m_32 = 0.0
            self.m_33 = 1.0
            self.m_34 = 0.0
            self.m_41 = 0.0
            self.m_42 = 0.0
            self.m_43 = 0.0
            self.m_44 = 1.0

        def is_identity(self):
            """Return ``True`` if the matrix is close to identity."""
            if (abs(self.m_11 - 1.0) > CgfFormat.EPSILON
                or abs(self.m_12) > CgfFormat.EPSILON
                or abs(self.m_13) > CgfFormat.EPSILON
                or abs(self.m_14) > CgfFormat.EPSILON
                or abs(self.m_21) > CgfFormat.EPSILON
                or abs(self.m_22 - 1.0) > CgfFormat.EPSILON
                or abs(self.m_23) > CgfFormat.EPSILON
                or abs(self.m_24) > CgfFormat.EPSILON
                or abs(self.m_31) > CgfFormat.EPSILON
                or abs(self.m_32) > CgfFormat.EPSILON
                or abs(self.m_33 - 1.0) > CgfFormat.EPSILON
                or abs(self.m_34) > CgfFormat.EPSILON
                or abs(self.m_41) > CgfFormat.EPSILON
                or abs(self.m_42) > CgfFormat.EPSILON
                or abs(self.m_43) > CgfFormat.EPSILON
                or abs(self.m_44 - 1.0) > CgfFormat.EPSILON):
                return False
            else:
                return True

        def get_copy(self):
            """Create a copy of the matrix."""
            mat = CgfFormat.Matrix44()
            mat.m_11 = self.m_11
            mat.m_12 = self.m_12
            mat.m_13 = self.m_13
            mat.m_14 = self.m_14
            mat.m_21 = self.m_21
            mat.m_22 = self.m_22
            mat.m_23 = self.m_23
            mat.m_24 = self.m_24
            mat.m_31 = self.m_31
            mat.m_32 = self.m_32
            mat.m_33 = self.m_33
            mat.m_34 = self.m_34
            mat.m_41 = self.m_41
            mat.m_42 = self.m_42
            mat.m_43 = self.m_43
            mat.m_44 = self.m_44
            return mat

        def get_matrix_33(self):
            """Returns upper left 3x3 part."""
            m = CgfFormat.Matrix33()
            m.m_11 = self.m_11
            m.m_12 = self.m_12
            m.m_13 = self.m_13
            m.m_21 = self.m_21
            m.m_22 = self.m_22
            m.m_23 = self.m_23
            m.m_31 = self.m_31
            m.m_32 = self.m_32
            m.m_33 = self.m_33
            return m

        def set_matrix_33(self, m):
            """Sets upper left 3x3 part."""
            if not isinstance(m, CgfFormat.Matrix33):
                raise TypeError('argument must be Matrix33')
            self.m_11 = m.m_11
            self.m_12 = m.m_12
            self.m_13 = m.m_13
            self.m_21 = m.m_21
            self.m_22 = m.m_22
            self.m_23 = m.m_23
            self.m_31 = m.m_31
            self.m_32 = m.m_32
            self.m_33 = m.m_33

        def get_translation(self):
            """Returns lower left 1x3 part."""
            t = CgfFormat.Vector3()
            t.x = self.m_41
            t.y = self.m_42
            t.z = self.m_43
            return t

        def set_translation(self, translation):
            """Returns lower left 1x3 part."""
            if not isinstance(translation, CgfFormat.Vector3):
                raise TypeError('argument must be Vector3')
            self.m_41 = translation.x
            self.m_42 = translation.y
            self.m_43 = translation.z

        def is_scale_rotation_translation(self):
            if not self.get_matrix_33().is_scale_rotation(): return False
            if abs(self.m_14) > CgfFormat.EPSILON: return False
            if abs(self.m_24) > CgfFormat.EPSILON: return False
            if abs(self.m_34) > CgfFormat.EPSILON: return False
            if abs(self.m_44 - 1.0) > CgfFormat.EPSILON: return False
            return True

        def get_scale_rotation_translation(self):
            rotscl = self.get_matrix_33()
            scale, rot = rotscl.get_scale_rotation()
            trans = self.get_translation()
            return (scale, rot, trans)

        def get_scale_quat_translation(self):
            rotscl = self.get_matrix_33()
            scale, quat = rotscl.get_scale_quat()
            trans = self.get_translation()
            return (scale, quat, trans)

        def set_scale_rotation_translation(self, scale, rotation, translation):
            if not isinstance(scale, CgfFormat.Vector3):
                raise TypeError('scale must be Vector3')
            if not isinstance(rotation, CgfFormat.Matrix33):
                raise TypeError('rotation must be Matrix33')
            if not isinstance(translation, CgfFormat.Vector3):
                raise TypeError('translation must be Vector3')

            if not rotation.is_rotation():
                logger = logging.getLogger("pyffi.cgf.matrix")
                mat = rotation * rotation.get_transpose()
                idmat = CgfFormat.Matrix33()
                idmat.set_identity()
                error = (mat - idmat).sup_norm()
                logger.warning("improper rotation matrix (error is %f)" % error)
                logger.debug("  matrix =")
                for line in str(rotation).split("\n"):
                    logger.debug("    %s" % line)
                logger.debug("  its determinant = %f" % rotation.get_determinant())
                logger.debug("  matrix * matrix^T =")
                for line in str(mat).split("\n"):
                    logger.debug("    %s" % line)

            self.m_14 = 0.0
            self.m_24 = 0.0
            self.m_34 = 0.0
            self.m_44 = 1.0

            self.set_matrix_33(rotation * scale)
            self.set_translation(translation)

        def get_inverse(self, fast=True):
            """Calculates inverse (fast assumes is_scale_rotation_translation is True)."""
            def adjoint(m, ii, jj):
                result = []
                for i, row in enumerate(m):
                    if i == ii: continue
                    result.append([])
                    for j, x in enumerate(row):
                        if j == jj: continue
                        result[-1].append(x)
                return result
            def determinant(m):
                if len(m) == 2:
                    return m[0][0]*m[1][1] - m[1][0]*m[0][1]
                result = 0.0
                for i in xrange(len(m)):
                    det = determinant(adjoint(m, i, 0))
                    if i & 1:
                        result -= m[i][0] * det
                    else:
                        result += m[i][0] * det
                return result

            if fast:
                m = self.get_matrix_33().get_inverse()
                t = -(self.get_translation() * m)

                n = CgfFormat.Matrix44()
                n.m_14 = 0.0
                n.m_24 = 0.0
                n.m_34 = 0.0
                n.m_44 = 1.0
                n.set_matrix_33(m)
                n.set_translation(t)
                return n
            else:
                m = self.as_list()
                nn = [[0.0 for i in xrange(4)] for j in xrange(4)]
                det = determinant(m)
                if abs(det) < CgfFormat.EPSILON:
                    raise ZeroDivisionError('cannot invert matrix:\n%s'%self)
                for i in xrange(4):
                    for j in xrange(4):
                        if (i+j) & 1:
                            nn[j][i] = -determinant(adjoint(m, i, j)) / det
                        else:
                            nn[j][i] = determinant(adjoint(m, i, j)) / det
                n = CgfFormat.Matrix44()
                n.set_rows(*nn)
                return n

        def __mul__(self, x):
            if isinstance(x, (float, int, long)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 * x
                m.m_12 = self.m_12 * x
                m.m_13 = self.m_13 * x
                m.m_14 = self.m_14 * x
                m.m_21 = self.m_21 * x
                m.m_22 = self.m_22 * x
                m.m_23 = self.m_23 * x
                m.m_24 = self.m_24 * x
                m.m_31 = self.m_31 * x
                m.m_32 = self.m_32 * x
                m.m_33 = self.m_33 * x
                m.m_34 = self.m_34 * x
                m.m_41 = self.m_41 * x
                m.m_42 = self.m_42 * x
                m.m_43 = self.m_43 * x
                m.m_44 = self.m_44 * x
                return m
            elif isinstance(x, CgfFormat.Vector3):
                raise TypeError("matrix*vector not supported; please use left multiplication (vector*matrix)")
            elif isinstance(x, CgfFormat.Vector4):
                raise TypeError("matrix*vector not supported; please use left multiplication (vector*matrix)")
            elif isinstance(x, CgfFormat.Matrix44):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 * x.m_11  +  self.m_12 * x.m_21  +  self.m_13 * x.m_31  +  self.m_14 * x.m_41
                m.m_12 = self.m_11 * x.m_12  +  self.m_12 * x.m_22  +  self.m_13 * x.m_32  +  self.m_14 * x.m_42
                m.m_13 = self.m_11 * x.m_13  +  self.m_12 * x.m_23  +  self.m_13 * x.m_33  +  self.m_14 * x.m_43
                m.m_14 = self.m_11 * x.m_14  +  self.m_12 * x.m_24  +  self.m_13 * x.m_34  +  self.m_14 * x.m_44
                m.m_21 = self.m_21 * x.m_11  +  self.m_22 * x.m_21  +  self.m_23 * x.m_31  +  self.m_24 * x.m_41
                m.m_22 = self.m_21 * x.m_12  +  self.m_22 * x.m_22  +  self.m_23 * x.m_32  +  self.m_24 * x.m_42
                m.m_23 = self.m_21 * x.m_13  +  self.m_22 * x.m_23  +  self.m_23 * x.m_33  +  self.m_24 * x.m_43
                m.m_24 = self.m_21 * x.m_14  +  self.m_22 * x.m_24  +  self.m_23 * x.m_34  +  self.m_24 * x.m_44
                m.m_31 = self.m_31 * x.m_11  +  self.m_32 * x.m_21  +  self.m_33 * x.m_31  +  self.m_34 * x.m_41
                m.m_32 = self.m_31 * x.m_12  +  self.m_32 * x.m_22  +  self.m_33 * x.m_32  +  self.m_34 * x.m_42
                m.m_33 = self.m_31 * x.m_13  +  self.m_32 * x.m_23  +  self.m_33 * x.m_33  +  self.m_34 * x.m_43
                m.m_34 = self.m_31 * x.m_14  +  self.m_32 * x.m_24  +  self.m_33 * x.m_34  +  self.m_34 * x.m_44
                m.m_41 = self.m_41 * x.m_11  +  self.m_42 * x.m_21  +  self.m_43 * x.m_31  +  self.m_44 * x.m_41
                m.m_42 = self.m_41 * x.m_12  +  self.m_42 * x.m_22  +  self.m_43 * x.m_32  +  self.m_44 * x.m_42
                m.m_43 = self.m_41 * x.m_13  +  self.m_42 * x.m_23  +  self.m_43 * x.m_33  +  self.m_44 * x.m_43
                m.m_44 = self.m_41 * x.m_14  +  self.m_42 * x.m_24  +  self.m_43 * x.m_34  +  self.m_44 * x.m_44
                return m
            else:
                raise TypeError("do not know how to multiply Matrix44 with %s"%x.__class__)

        def __div__(self, x):
            if isinstance(x, (float, int, long)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 / x
                m.m_12 = self.m_12 / x
                m.m_13 = self.m_13 / x
                m.m_14 = self.m_14 / x
                m.m_21 = self.m_21 / x
                m.m_22 = self.m_22 / x
                m.m_23 = self.m_23 / x
                m.m_24 = self.m_24 / x
                m.m_31 = self.m_31 / x
                m.m_32 = self.m_32 / x
                m.m_33 = self.m_33 / x
                m.m_34 = self.m_34 / x
                m.m_41 = self.m_41 / x
                m.m_42 = self.m_42 / x
                m.m_43 = self.m_43 / x
                m.m_44 = self.m_44 / x
                return m
            else:
                raise TypeError("do not know how to divide Matrix44 by %s"%x.__class__)

        def __rmul__(self, x):
            if isinstance(x, (float, int, long)):
                return self * x
            else:
                raise TypeError("do not know how to multiply %s with Matrix44"%x.__class__)

        def __eq__(self, m):
            if isinstance(m, type(None)):
                return False
            if not isinstance(m, CgfFormat.Matrix44):
                raise TypeError("do not know how to compare Matrix44 and %s"%m.__class__)
            if abs(self.m_11 - m.m_11) > CgfFormat.EPSILON: return False
            if abs(self.m_12 - m.m_12) > CgfFormat.EPSILON: return False
            if abs(self.m_13 - m.m_13) > CgfFormat.EPSILON: return False
            if abs(self.m_14 - m.m_14) > CgfFormat.EPSILON: return False
            if abs(self.m_21 - m.m_21) > CgfFormat.EPSILON: return False
            if abs(self.m_22 - m.m_22) > CgfFormat.EPSILON: return False
            if abs(self.m_23 - m.m_23) > CgfFormat.EPSILON: return False
            if abs(self.m_24 - m.m_24) > CgfFormat.EPSILON: return False
            if abs(self.m_31 - m.m_31) > CgfFormat.EPSILON: return False
            if abs(self.m_32 - m.m_32) > CgfFormat.EPSILON: return False
            if abs(self.m_33 - m.m_33) > CgfFormat.EPSILON: return False
            if abs(self.m_34 - m.m_34) > CgfFormat.EPSILON: return False
            if abs(self.m_41 - m.m_41) > CgfFormat.EPSILON: return False
            if abs(self.m_42 - m.m_42) > CgfFormat.EPSILON: return False
            if abs(self.m_43 - m.m_43) > CgfFormat.EPSILON: return False
            if abs(self.m_44 - m.m_44) > CgfFormat.EPSILON: return False
            return True

        def __ne__(self, m):
            return not self.__eq__(m)

        def __add__(self, x):
            if isinstance(x, (CgfFormat.Matrix44)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 + x.m_11
                m.m_12 = self.m_12 + x.m_12
                m.m_13 = self.m_13 + x.m_13
                m.m_14 = self.m_14 + x.m_14
                m.m_21 = self.m_21 + x.m_21
                m.m_22 = self.m_22 + x.m_22
                m.m_23 = self.m_23 + x.m_23
                m.m_24 = self.m_24 + x.m_24
                m.m_31 = self.m_31 + x.m_31
                m.m_32 = self.m_32 + x.m_32
                m.m_33 = self.m_33 + x.m_33
                m.m_34 = self.m_34 + x.m_34
                m.m_41 = self.m_41 + x.m_41
                m.m_42 = self.m_42 + x.m_42
                m.m_43 = self.m_43 + x.m_43
                m.m_44 = self.m_44 + x.m_44
                return m
            elif isinstance(x, (int, long, float)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 + x
                m.m_12 = self.m_12 + x
                m.m_13 = self.m_13 + x
                m.m_14 = self.m_14 + x
                m.m_21 = self.m_21 + x
                m.m_22 = self.m_22 + x
                m.m_23 = self.m_23 + x
                m.m_24 = self.m_24 + x
                m.m_31 = self.m_31 + x
                m.m_32 = self.m_32 + x
                m.m_33 = self.m_33 + x
                m.m_34 = self.m_34 + x
                m.m_41 = self.m_41 + x
                m.m_42 = self.m_42 + x
                m.m_43 = self.m_43 + x
                m.m_44 = self.m_44 + x
                return m
            else:
                raise TypeError("do not know how to add Matrix44 and %s"%x.__class__)

        def __sub__(self, x):
            if isinstance(x, (CgfFormat.Matrix44)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 - x.m_11
                m.m_12 = self.m_12 - x.m_12
                m.m_13 = self.m_13 - x.m_13
                m.m_14 = self.m_14 - x.m_14
                m.m_21 = self.m_21 - x.m_21
                m.m_22 = self.m_22 - x.m_22
                m.m_23 = self.m_23 - x.m_23
                m.m_24 = self.m_24 - x.m_24
                m.m_31 = self.m_31 - x.m_31
                m.m_32 = self.m_32 - x.m_32
                m.m_33 = self.m_33 - x.m_33
                m.m_34 = self.m_34 - x.m_34
                m.m_41 = self.m_41 - x.m_41
                m.m_42 = self.m_42 - x.m_42
                m.m_43 = self.m_43 - x.m_43
                m.m_44 = self.m_44 - x.m_44
                return m
            elif isinstance(x, (int, long, float)):
                m = CgfFormat.Matrix44()
                m.m_11 = self.m_11 - x
                m.m_12 = self.m_12 - x
                m.m_13 = self.m_13 - x
                m.m_14 = self.m_14 - x
                m.m_21 = self.m_21 - x
                m.m_22 = self.m_22 - x
                m.m_23 = self.m_23 - x
                m.m_24 = self.m_24 - x
                m.m_31 = self.m_31 - x
                m.m_32 = self.m_32 - x
                m.m_33 = self.m_33 - x
                m.m_34 = self.m_34 - x
                m.m_41 = self.m_41 - x
                m.m_42 = self.m_42 - x
                m.m_43 = self.m_43 - x
                m.m_44 = self.m_44 - x
                return m
            else:
                raise TypeError("do not know how to substract Matrix44 and %s"
                                % x.__class__)

        def sup_norm(self):
            """Calculate supremum norm of matrix (maximum absolute value of all
            entries)."""
            return max(max(abs(elem) for elem in row)
                       for row in self.as_list())

    class MeshChunk:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            for vert in self.vertices:
                vert.p.x *= scale
                vert.p.y *= scale
                vert.p.z *= scale

            self.min_bound.x *= scale
            self.min_bound.y *= scale
            self.min_bound.z *= scale
            self.max_bound.x *= scale
            self.max_bound.y *= scale
            self.max_bound.z *= scale

        def get_vertices(self):
            """Generator for all vertices."""
            if self.vertices:
                for vert in self.vertices:
                    yield vert.p
            elif self.vertices_data:
                for vert in self.vertices_data.vertices:
                    yield vert

        def get_normals(self):
            """Generator for all normals."""
            if self.vertices:
                for vert in self.vertices:
                    yield vert.n
            elif self.normals_data:
                for norm in self.normals_data.normals:
                    yield norm

        def get_colors(self):
            """Generator for all vertex colors."""
            if self.vertex_colors:
                for color in self.vertex_colors:
                    # Far Cry has no alpha channel
                    yield (color.r, color.g, color.b, 255)
            elif self.colors_data:
                if self.colors_data.rgb_colors:
                    for color in self.colors_data.rgb_colors:
                        yield (color.r, color.g, color.b, 255)
                elif self.colors_data.rgba_colors:
                    for color in self.colors_data.rgba_colors:
                        yield (color.r, color.g, color.b, color.a)

        def get_num_triangles(self):
            """Get number of triangles."""
            if self.faces:
                return self.num_faces
            elif self.indices_data:
                return self.indices_data.num_elements // 3
            else:
                return 0

        def get_triangles(self):
            """Generator for all triangles."""
            if self.faces:
                for face in self.faces:
                    yield face.v_0, face.v_1, face.v_2
            elif self.indices_data:
                it = iter(self.indices_data.indices)
                while True:
                   yield it.next(), it.next(), it.next()

        def get_material_indices(self):
            """Generator for all materials (per triangle)."""
            if self.faces:
                for face in self.faces:
                    yield face.material
            elif self.mesh_subsets:
                for meshsubset in self.mesh_subsets.mesh_subsets:
                    for i in xrange(meshsubset.num_indices // 3):
                        yield meshsubset.mat_id

        def get_uvs(self):
            """Generator for all uv coordinates."""
            if self.uvs:
                for uv in self.uvs:
                    yield uv.u, uv.v
            elif self.uvs_data:
                for uv in self.uvs_data.uvs:
                    yield uv.u, 1.0 - uv.v # OpenGL fix!

        def get_uv_triangles(self):
            """Generator for all uv triangles."""
            if self.uv_faces:
                for uvface in self.uv_faces:
                    yield uvface.t_0, uvface.t_1, uvface.t_2
            elif self.indices_data:
                # Crysis: UV triangles coincide with triangles
                it = iter(self.indices_data.indices)
                while True:
                    yield it.next(), it.next(), it.next()

        ### DEPRECATED: USE set_geometry INSTEAD ###
        def set_vertices_normals(self, vertices, normals):
            """B{Deprecated. Use L{set_geometry} instead.} Set vertices and normals. This used to be the first function to call
            when setting mesh geometry data.

            Returns list of chunks that have been added."""
            # Far Cry
            self.num_vertices = len(vertices)
            self.vertices.update_size()

            # Crysis
            self.vertices_data = CgfFormat.DataStreamChunk()
            self.vertices_data.data_stream_type = CgfFormat.DataStreamType.VERTICES
            self.vertices_data.bytes_per_element = 12
            self.vertices_data.num_elements = len(vertices)
            self.vertices_data.vertices.update_size()

            self.normals_data = CgfFormat.DataStreamChunk()
            self.normals_data.data_stream_type = CgfFormat.DataStreamType.NORMALS
            self.normals_data.bytes_per_element = 12
            self.normals_data.num_elements = len(vertices)
            self.normals_data.normals.update_size()

            # set vertex coordinates and normals for Far Cry
            for cryvert, vert, norm in izip(self.vertices, vertices, normals):
                cryvert.p.x = vert[0]
                cryvert.p.y = vert[1]
                cryvert.p.z = vert[2]
                cryvert.n.x = norm[0]
                cryvert.n.y = norm[1]
                cryvert.n.z = norm[2]

            # set vertex coordinates and normals for Crysis
            for cryvert, crynorm, vert, norm in izip(self.vertices_data.vertices,
                                                     self.normals_data.normals,
                                                     vertices, normals):
                cryvert.x = vert[0]
                cryvert.y = vert[1]
                cryvert.z = vert[2]
                crynorm.x = norm[0]
                crynorm.y = norm[1]
                crynorm.z = norm[2]

        ### STILL WIP!!! ###
        def set_geometry(self,
                        verticeslist = None, normalslist = None,
                        triangleslist = None, matlist = None,
                        uvslist = None, colorslist = None):
            """Set geometry data.

            >>> from pyffi.formats.cgf import CgfFormat
            >>> chunk = CgfFormat.MeshChunk()
            >>> vertices1 = [(0,0,0),(0,1,0),(1,0,0),(1,1,0)]
            >>> vertices2 = [(0,0,1),(0,1,1),(1,0,1),(1,1,1)]
            >>> normals1 = [(0,0,-1),(0,0,-1),(0,0,-1),(0,0,-1)]
            >>> normals2 = [(0,0,1),(0,0,1),(0,0,1),(0,0,1)]
            >>> triangles1 = [(0,1,2),(2,1,3)]
            >>> triangles2 = [(0,1,2),(2,1,3)]
            >>> uvs1 = [(0,0),(0,1),(1,0),(1,1)]
            >>> uvs2 = [(0,0),(0,1),(1,0),(1,1)]
            >>> colors1 = [(0,1,2,3),(4,5,6,7),(8,9,10,11),(12,13,14,15)]
            >>> colors_2 = [(50,51,52,53),(54,55,56,57),(58,59,60,61),(62,63,64,65)]
            >>> chunk.set_geometry(verticeslist = [vertices1, vertices2],
            ...                   normalslist = [normals1, normals2],
            ...                   triangleslist = [triangles1, triangles2],
            ...                   uvslist = [uvs1, uvs2],
            ...                   matlist = [2,5],
            ...                   colorslist = [colors1, colors_2])
            >>> print(chunk) # doctest: +ELLIPSIS +REPORT_UDIFF
            <class 'pyffi.formats.cgf.MeshChunk'> instance at ...
            * has_vertex_weights : False
            * has_vertex_colors : True
            * in_world_space : False
            * reserved_1 : 0
            * reserved_2 : 0
            * flags_1 : 0
            * flags_2 : 0
            * num_vertices : 8
            * num_indices : 12
            * num_uvs : 8
            * num_faces : 4
            * material : None
            * num_mesh_subsets : 2
            * mesh_subsets : <class 'pyffi.formats.cgf.MeshSubsetsChunk'> instance at ...
            * vert_anim : None
            * vertices :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  0.000  0.000  0.000 ]
                * n : [  0.000  0.000 -1.000 ]
                1: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  0.000  1.000  0.000 ]
                * n : [  0.000  0.000 -1.000 ]
                2: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  1.000  0.000  0.000 ]
                * n : [  0.000  0.000 -1.000 ]
                3: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  1.000  1.000  0.000 ]
                * n : [  0.000  0.000 -1.000 ]
                4: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  0.000  0.000  1.000 ]
                * n : [  0.000  0.000  1.000 ]
                5: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  0.000  1.000  1.000 ]
                * n : [  0.000  0.000  1.000 ]
                6: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  1.000  0.000  1.000 ]
                * n : [  0.000  0.000  1.000 ]
                7: <class 'pyffi.formats.cgf.Vertex'> instance at ...
                * p : [  1.000  1.000  1.000 ]
                * n : [  0.000  0.000  1.000 ]
            * faces :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.Face'> instance at ...
                * v_0 : 0
                * v_1 : 1
                * v_2 : 2
                * material : 2
                * sm_group : 1
                1: <class 'pyffi.formats.cgf.Face'> instance at ...
                * v_0 : 2
                * v_1 : 1
                * v_2 : 3
                * material : 2
                * sm_group : 1
                2: <class 'pyffi.formats.cgf.Face'> instance at ...
                * v_0 : 4
                * v_1 : 5
                * v_2 : 6
                * material : 5
                * sm_group : 1
                3: <class 'pyffi.formats.cgf.Face'> instance at ...
                * v_0 : 6
                * v_1 : 5
                * v_2 : 7
                * material : 5
                * sm_group : 1
            * uvs :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 0.0
                1: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 1.0
                2: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 0.0
                3: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 1.0
                4: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 0.0
                5: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 1.0
                6: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 0.0
                7: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 1.0
            * uv_faces :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.UVFace'> instance at ...
                * t_0 : 0
                * t_1 : 1
                * t_2 : 2
                1: <class 'pyffi.formats.cgf.UVFace'> instance at ...
                * t_0 : 2
                * t_1 : 1
                * t_2 : 3
                2: <class 'pyffi.formats.cgf.UVFace'> instance at ...
                * t_0 : 4
                * t_1 : 5
                * t_2 : 6
                3: <class 'pyffi.formats.cgf.UVFace'> instance at ...
                * t_0 : 6
                * t_1 : 5
                * t_2 : 7
            * vertex_colors :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 0
                * g : 1
                * b : 2
                1: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 4
                * g : 5
                * b : 6
                2: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 8
                * g : 9
                * b : 10
                3: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 12
                * g : 13
                * b : 14
                4: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 50
                * g : 51
                * b : 52
                5: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 54
                * g : 55
                * b : 56
                6: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 58
                * g : 59
                * b : 60
                7: <class 'pyffi.formats.cgf.IRGB'> instance at ...
                * r : 62
                * g : 63
                * b : 64
            * vertices_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * normals_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * uvs_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * colors_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * colors_2_data : None
            * indices_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * tangents_data : <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * sh_coeffs_data : None
            * shape_deformation_data : None
            * bone_map_data : None
            * face_map_data : None
            * vert_mats_data : None
            * reserved_data :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: None
                1: None
                2: None
                3: None
            * physics_data :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: None
                1: None
                2: None
                3: None
            * min_bound : [  0.000  0.000  0.000 ]
            * max_bound : [  1.000  1.000  1.000 ]
            * reserved_3 :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: 0
                1: 0
                2: 0
                3: 0
                4: 0
                5: 0
                6: 0
                7: 0
                8: 0
                9: 0
                10: 0
                11: 0
                12: 0
                13: 0
                14: 0
                15: 0
                16: 0
                etc...
            <BLANKLINE>
            >>> print(chunk.mesh_subsets) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.MeshSubsetsChunk'> instance at ...
            * flags :
                <class 'pyffi.formats.cgf.MeshSubsetsFlags'> instance at ...
                * sh_has_decompr_mat : 0
                * bone_indices : 0
            * num_mesh_subsets : 2
            * reserved_1 : 0
            * reserved_2 : 0
            * reserved_3 : 0
            * mesh_subsets :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.MeshSubset'> instance at ...
                * first_index : 0
                * num_indices : 6
                * first_vertex : 0
                * num_vertices : 4
                * mat_id : 2
                * radius : 0.7071067...
                * center : [  0.500  0.500  0.000 ]
                1: <class 'pyffi.formats.cgf.MeshSubset'> instance at ...
                * first_index : 6
                * num_indices : 6
                * first_vertex : 4
                * num_vertices : 4
                * mat_id : 5
                * radius : 0.7071067...
                * center : [  0.500  0.500  1.000 ]
            <BLANKLINE>
            >>> print(chunk.vertices_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : VERTICES
            * num_elements : 8
            * bytes_per_element : 12
            * reserved_1 : 0
            * reserved_2 : 0
            * vertices :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: [  0.000  0.000  0.000 ]
                1: [  0.000  1.000  0.000 ]
                2: [  1.000  0.000  0.000 ]
                3: [  1.000  1.000  0.000 ]
                4: [  0.000  0.000  1.000 ]
                5: [  0.000  1.000  1.000 ]
                6: [  1.000  0.000  1.000 ]
                7: [  1.000  1.000  1.000 ]
            <BLANKLINE>
            >>> print(chunk.normals_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : NORMALS
            * num_elements : 8
            * bytes_per_element : 12
            * reserved_1 : 0
            * reserved_2 : 0
            * normals :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: [  0.000  0.000 -1.000 ]
                1: [  0.000  0.000 -1.000 ]
                2: [  0.000  0.000 -1.000 ]
                3: [  0.000  0.000 -1.000 ]
                4: [  0.000  0.000  1.000 ]
                5: [  0.000  0.000  1.000 ]
                6: [  0.000  0.000  1.000 ]
                7: [  0.000  0.000  1.000 ]
            <BLANKLINE>
            >>> print(chunk.indices_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : INDICES
            * num_elements : 12
            * bytes_per_element : 2
            * reserved_1 : 0
            * reserved_2 : 0
            * indices :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: 0
                1: 1
                2: 2
                3: 2
                4: 1
                5: 3
                6: 4
                7: 5
                8: 6
                9: 6
                10: 5
                11: 7
            <BLANKLINE>
            >>> print(chunk.uvs_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : UVS
            * num_elements : 8
            * bytes_per_element : 8
            * reserved_1 : 0
            * reserved_2 : 0
            * uvs :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 1.0
                1: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 0.0
                2: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 1.0
                3: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 0.0
                4: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 1.0
                5: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 0.0
                * v : 0.0
                6: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 1.0
                7: <class 'pyffi.formats.cgf.UV'> instance at ...
                * u : 1.0
                * v : 0.0
            <BLANKLINE>
            >>> print(chunk.tangents_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : TANGENTS
            * num_elements : 8
            * bytes_per_element : 16
            * reserved_1 : 0
            * reserved_2 : 0
            * tangents :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                0, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                1, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                1, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                2, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                2, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                3, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                3, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                4, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                4, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                5, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                5, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                6, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                6, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
                7, 0: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 32767
                * y : 0
                * z : 0
                * w : 32767
                7, 1: <class 'pyffi.formats.cgf.Tangent'> instance at ...
                * x : 0
                * y : -32767
                * z : 0
                * w : 32767
            <BLANKLINE>
            >>> print(chunk.colors_data) # doctest: +ELLIPSIS
            <class 'pyffi.formats.cgf.DataStreamChunk'> instance at ...
            * flags : 0
            * data_stream_type : COLORS
            * num_elements : 8
            * bytes_per_element : 4
            * reserved_1 : 0
            * reserved_2 : 0
            * rgba_colors :
                <class 'pyffi.object_models.xml.array.Array'> instance at ...
                0: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 0
                * g : 1
                * b : 2
                * a : 3
                1: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 4
                * g : 5
                * b : 6
                * a : 7
                2: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 8
                * g : 9
                * b : 10
                * a : 11
                3: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 12
                * g : 13
                * b : 14
                * a : 15
                4: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 50
                * g : 51
                * b : 52
                * a : 53
                5: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 54
                * g : 55
                * b : 56
                * a : 57
                6: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 58
                * g : 59
                * b : 60
                * a : 61
                7: <class 'pyffi.formats.cgf.IRGBA'> instance at ...
                * r : 62
                * g : 63
                * b : 64
                * a : 65
            <BLANKLINE>

            :param verticeslist: A list of lists of vertices (one list per material).
            :param normalslist: A list of lists of normals (one list per material).
            :param triangleslist: A list of lists of triangles (one list per material).
            :param matlist: A list of material indices. Optional.
            :param uvslist: A list of lists of uvs (one list per material). Optional.
            :param colorslist: A list of lists of RGBA colors (one list per material).
                Optional. Each color is a tuple (r, g, b, a) with each component an
                integer between 0 and 255.
            """
            # argument sanity checking
            # check length of lists
            if len(verticeslist) != len(normalslist):
                raise ValueError("normalslist must have same length as verticeslist")
            if len(triangleslist) != len(normalslist):
                raise ValueError("triangleslist must have same length as verticeslist")
            if not matlist is None and len(verticeslist) != len(matlist):
                raise ValueError("matlist must have same length as verticeslist")
            if not uvslist is None and len(verticeslist) != len(uvslist):
                raise ValueError("uvslist must have same length as verticeslist")
            if not colorslist is None and len(verticeslist) != len(colorslist):
                raise ValueError("colorslist must have same length as verticeslist")

            # check length of lists in lists
            for vertices, normals in izip(verticeslist, normalslist):
                if len(vertices) != len(normals):
                    raise ValueError("vertex and normal lists must have same length")
            if not uvslist is None:
                for vertices, uvs in izip(verticeslist, uvslist):
                    if len(vertices) != len(uvs):
                        raise ValueError("vertex and uv lists must have same length")
            if not colorslist is None:
                for vertices, colors in izip(verticeslist, colorslist):
                    if len(vertices) != len(colors):
                        raise ValueError("vertex and color lists must have same length")

            # get total number of vertices
            numvertices = sum(len(vertices) for vertices in verticeslist)
            if numvertices > 65535:
                raise ValueError("cannot store geometry: too many vertices (%i and maximum is 65535)" % numvertices)
            numtriangles = sum(len(triangles) for triangles in triangleslist)

            # Far Cry data preparation
            self.num_vertices = numvertices
            self.vertices.update_size()
            selfvertices_iter = iter(self.vertices)
            self.num_faces = numtriangles
            self.faces.update_size()
            selffaces_iter = iter(self.faces)
            if not uvslist is None:
                self.num_uvs = numvertices
                self.uvs.update_size()
                self.uv_faces.update_size()
                selfuvs_iter = iter(self.uvs)
                selfuv_faces_iter = iter(self.uv_faces)
            if not colorslist is None:
                self.has_vertex_colors = True
                self.vertex_colors.update_size()
                selfvertex_colors_iter = iter(self.vertex_colors)

            # Crysis data preparation
            self.num_indices = numtriangles * 3

            self.vertices_data = CgfFormat.DataStreamChunk()
            self.vertices_data.data_stream_type = CgfFormat.DataStreamType.VERTICES
            self.vertices_data.bytes_per_element = 12
            self.vertices_data.num_elements = numvertices
            self.vertices_data.vertices.update_size()
            selfvertices_data_iter = iter(self.vertices_data.vertices)

            self.normals_data = CgfFormat.DataStreamChunk()
            self.normals_data.data_stream_type = CgfFormat.DataStreamType.NORMALS
            self.normals_data.bytes_per_element = 12
            self.normals_data.num_elements = numvertices
            self.normals_data.normals.update_size()
            selfnormals_data_iter = iter(self.normals_data.normals)

            self.indices_data = CgfFormat.DataStreamChunk()
            self.indices_data.data_stream_type = CgfFormat.DataStreamType.INDICES
            self.indices_data.bytes_per_element = 2
            self.indices_data.num_elements = numtriangles * 3
            self.indices_data.indices.update_size()

            if not uvslist is None:
                # uvs
                self.uvs_data = CgfFormat.DataStreamChunk()
                self.uvs_data.data_stream_type = CgfFormat.DataStreamType.UVS
                self.uvs_data.bytes_per_element = 8
                self.uvs_data.num_elements = numvertices
                self.uvs_data.uvs.update_size()
                selfuvs_data_iter = iter(self.uvs_data.uvs)
                # have tangent space
                has_tangentspace = True
            else:
                # no tangent space
                has_tangentspace = False

            if not colorslist is None:
                # vertex colors
                self.colors_data = CgfFormat.DataStreamChunk()
                self.colors_data.data_stream_type = CgfFormat.DataStreamType.COLORS
                self.colors_data.bytes_per_element = 4
                self.colors_data.num_elements = numvertices
                self.colors_data.rgba_colors.update_size()
                selfcolors_data_iter = iter(self.colors_data.rgba_colors)

            self.num_mesh_subsets = len(verticeslist)
            self.mesh_subsets = CgfFormat.MeshSubsetsChunk()
            self.mesh_subsets.num_mesh_subsets = self.num_mesh_subsets
            self.mesh_subsets.mesh_subsets.update_size()

            # set up default iterators
            if matlist is None:
                matlist = itertools.repeat(0)
            if uvslist is None:
                uvslist = itertools.repeat(None)
            if colorslist is None:
                colorslist = itertools.repeat(None)

            # now iterate over all materials
            firstvertexindex = 0
            firstindicesindex = 0
            for vertices, normals, triangles, mat, uvs, colors, meshsubset in izip(
                verticeslist, normalslist,
                triangleslist, matlist,
                uvslist, colorslist,
                self.mesh_subsets.mesh_subsets):

                # set Crysis mesh subset info
                meshsubset.first_index = firstindicesindex
                meshsubset.num_indices = len(triangles) * 3
                meshsubset.first_vertex = firstvertexindex
                meshsubset.num_vertices = len(vertices)
                meshsubset.mat_id = mat
                center, radius = pyffi.utils.mathutils.getCenterRadius(vertices)
                meshsubset.radius = radius
                meshsubset.center.x = center[0]
                meshsubset.center.y = center[1]
                meshsubset.center.z = center[2]

                # set vertex coordinates and normals for Far Cry
                for vert, norm in izip(vertices, normals):
                    cryvert = selfvertices_iter.next()
                    cryvert.p.x = vert[0]
                    cryvert.p.y = vert[1]
                    cryvert.p.z = vert[2]
                    cryvert.n.x = norm[0]
                    cryvert.n.y = norm[1]
                    cryvert.n.z = norm[2]

                # set vertex coordinates and normals for Crysis
                for vert, norm in izip(vertices, normals):
                    cryvert = selfvertices_data_iter.next()
                    crynorm = selfnormals_data_iter.next()
                    cryvert.x = vert[0]
                    cryvert.y = vert[1]
                    cryvert.z = vert[2]
                    crynorm.x = norm[0]
                    crynorm.y = norm[1]
                    crynorm.z = norm[2]

                # set Far Cry face info
                for triangle in triangles:
                    cryface = selffaces_iter.next()
                    cryface.v_0 = triangle[0] + firstvertexindex
                    cryface.v_1 = triangle[1] + firstvertexindex
                    cryface.v_2 = triangle[2] + firstvertexindex
                    cryface.material = mat

                # set Crysis face info
                for i, vertexindex in enumerate(itertools.chain(*triangles)):
                    self.indices_data.indices[i + firstindicesindex] \
                        = vertexindex + firstvertexindex

                if not uvs is None:
                    # set Far Cry uv info
                    for triangle in triangles:
                        cryuvface = selfuv_faces_iter.next()
                        cryuvface.t_0 = triangle[0] + firstvertexindex
                        cryuvface.t_1 = triangle[1] + firstvertexindex
                        cryuvface.t_2 = triangle[2] + firstvertexindex
                    for uv in uvs:
                        cryuv = selfuvs_iter.next()
                        cryuv.u = uv[0]
                        cryuv.v = uv[1]

                    # set Crysis uv info
                    for uv in uvs:
                        cryuv = selfuvs_data_iter.next()
                        cryuv.u = uv[0]
                        cryuv.v = 1.0 - uv[1] # OpenGL fix

                if not colors is None:
                    # set Far Cry color info
                    for color in colors:
                        crycolor = selfvertex_colors_iter.next()
                        crycolor.r = color[0]
                        crycolor.g = color[1]
                        crycolor.b = color[2]
                        # note: Far Cry does not support alpha color channel

                    # set Crysis color info
                    for color in colors:
                        crycolor = selfcolors_data_iter.next()
                        crycolor.r = color[0]
                        crycolor.g = color[1]
                        crycolor.b = color[2]
                        crycolor.a = color[3]

                # update index offsets
                firstvertexindex += len(vertices)
                firstindicesindex += 3 * len(triangles)

            # update tangent space
            if has_tangentspace:
                self.update_tangent_space()

            # set global bounding box
            minbound, maxbound = pyffi.utils.mathutils.getBoundingBox(
                list(itertools.chain(*verticeslist)))
            self.min_bound.x = minbound[0]
            self.min_bound.y = minbound[1]
            self.min_bound.z = minbound[2]
            self.max_bound.x = maxbound[0]
            self.max_bound.y = maxbound[1]
            self.max_bound.z = maxbound[2]

        def update_tangent_space(self):
            """Recalculate tangent space data."""
            # set up tangent space
            self.tangents_data = CgfFormat.DataStreamChunk()
            self.tangents_data.data_stream_type = CgfFormat.DataStreamType.TANGENTS
            self.tangents_data.bytes_per_element = 16
            self.tangents_data.num_elements = self.num_vertices
            self.tangents_data.tangents.update_size()
            selftangents_data_iter = iter(self.tangents_data.tangents)

            # set Crysis tangents info
            tangents, binormals, orientations = pyffi.utils.tangentspace.getTangentSpace(
                vertices = list((vert.x, vert.y, vert.z)
                                for vert in self.vertices_data.vertices),
                normals = list((norm.x, norm.y, norm.z)
                                for norm in self.normals_data.normals),
                uvs = list((uv.u, uv.v)
                           for uv in self.uvs_data.uvs),
                triangles = list(self.get_triangles()),
                orientation = True)

            for crytangent, tan, bin, orient in izip(self.tangents_data.tangents,
                                                     tangents, binormals, orientations):
                if orient > 0:
                    tangent_w = 32767
                else:
                    tangent_w = -32767
                crytangent[1].x = int(32767 * tan[0])
                crytangent[1].y = int(32767 * tan[1])
                crytangent[1].z = int(32767 * tan[2])
                crytangent[1].w = tangent_w
                crytangent[0].x = int(32767 * bin[0])
                crytangent[0].y = int(32767 * bin[1])
                crytangent[0].z = int(32767 * bin[2])
                crytangent[0].w = tangent_w

    class MeshMorphTargetChunk:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            for morphvert in self.morph_vertices:
                morphvert.vertex_target.x *= scale
                morphvert.vertex_target.y *= scale
                morphvert.vertex_target.z *= scale

        def get_global_node_parent(self):
            """Get the block parent (used for instance in the QSkope global view)."""
            return self.mesh

        def get_global_display(self):
            """Return a name for the block."""
            return self.target_name

    class MeshSubsetsChunk:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            for meshsubset in self.mesh_subsets:
                meshsubset.radius *= scale
                meshsubset.center.x *= scale
                meshsubset.center.y *= scale
                meshsubset.center.z *= scale

    class MtlChunk:
        def get_name_shader_script(self):
            """Extract name, shader, and script."""
            name = self.name
            shader_begin = name.find("(")
            shader_end = name.find(")")
            script_begin = name.find("/")
            if (script_begin != -1):
                if (name.count("/") != 1):
                    # must have exactly one script
                    raise ValueError("%s malformed, has multiple ""/"""%name)
                mtlscript = name[script_begin+1:]
            else:
                mtlscript = ""
            if (shader_begin != -1): # if a shader was specified
                mtl_end = shader_begin
                # must have exactly one shader
                if (name.count("(") != 1):
                    # some names are buggy and have "((" instead of "("
                    # like in jungle_camp_sleeping_barack
                    # here we handle that case
                    if name[shader_begin + 1] == "(" \
                       and name[shader_begin + 1:].count("(") == 1:
                        shader_begin += 1
                    else:
                        raise ValueError("%s malformed, has multiple ""("""%name)
                if (name.count(")") != 1):
                    raise ValueError("%s malformed, has multiple "")"""%name)
                # shader name should non-empty
                if shader_begin > shader_end:
                    raise ValueError("%s malformed, ""("" comes after "")"""%name)
                # script must be immediately followed by the material
                if (script_begin != -1) and (shader_end + 1 != script_begin):
                    raise ValueError("%s malformed, shader not followed by script"%name)
                mtlname = name[:mtl_end]
                mtlshader = name[shader_begin+1:shader_end]
            else:
                if script_begin != -1:
                    mtlname = name[:script_begin]
                else:
                    mtlname = name[:]
                mtlshader = ""
            return mtlname, mtlshader, mtlscript

    class NodeChunk:
        def get_global_node_parent(self):
            """Get the block parent (used for instance in the QSkope global view)."""
            return self.parent

        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < CgfFormat.EPSILON:
                return
            self.transform.m_41 *= scale
            self.transform.m_42 *= scale
            self.transform.m_43 *= scale
            self.pos.x *= scale
            self.pos.y *= scale
            self.pos.z *= scale

        def update_pos_rot_scl(self):
            """Update position, rotation, and scale, from the transform."""
            scale, quat, trans = self.transform.get_scale_quat_translation()
            self.pos.x = trans.x
            self.pos.y = trans.y
            self.pos.z = trans.z
            self.rot.x = quat.x
            self.rot.y = quat.y
            self.rot.z = quat.z
            self.rot.w = quat.w
            self.scl.x = scale.x
            self.scl.y = scale.y
            self.scl.z = scale.z

    class SourceInfoChunk:
        def get_global_display(self):
            """Return a name for the block."""
            idx = max(self.source_file.rfind("\\"), self.source_file.rfind("/"))
            return self.source_file[idx+1:]

    class TimingChunk:
        def get_global_display(self):
            """Return a name for the block."""
            return self.global_range.name

    class Vector3:
        def as_list(self):
            return [self.x, self.y, self.z]

        def as_tuple(self):
            return (self.x, self.y, self.z)

        def norm(self):
            return (self.x*self.x + self.y*self.y + self.z*self.z) ** 0.5

        def normalize(self):
            norm = self.norm()
            if norm < CgfFormat.EPSILON:
                raise ZeroDivisionError('cannot normalize vector %s'%self)
            self.x /= norm
            self.y /= norm
            self.z /= norm

        def get_copy(self):
            v = CgfFormat.Vector3()
            v.x = self.x
            v.y = self.y
            v.z = self.z
            return v

        def __str__(self):
            return "[ %6.3f %6.3f %6.3f ]"%(self.x, self.y, self.z)

        def __mul__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = self.x * x
                v.y = self.y * x
                v.z = self.z * x
                return v
            elif isinstance(x, CgfFormat.Vector3):
                return self.x * x.x + self.y * x.y + self.z * x.z
            elif isinstance(x, CgfFormat.Matrix33):
                v = CgfFormat.Vector3()
                v.x = self.x * x.m_11 + self.y * x.m_21 + self.z * x.m_31
                v.y = self.x * x.m_12 + self.y * x.m_22 + self.z * x.m_32
                v.z = self.x * x.m_13 + self.y * x.m_23 + self.z * x.m_33
                return v
            elif isinstance(x, CgfFormat.Matrix44):
                return self * x.get_matrix_33() + x.get_translation()
            else:
                raise TypeError("do not know how to multiply Vector3 with %s"%x.__class__)

        def __rmul__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = x * self.x
                v.y = x * self.y
                v.z = x * self.z
                return v
            else:
                raise TypeError("do not know how to multiply %s and Vector3"%x.__class__)

        def __div__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = self.x / x
                v.y = self.y / x
                v.z = self.z / x
                return v
            else:
                raise TypeError("do not know how to divide Vector3 and %s"%x.__class__)

        def __add__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = self.x + x
                v.y = self.y + x
                v.z = self.z + x
                return v
            elif isinstance(x, CgfFormat.Vector3):
                v = CgfFormat.Vector3()
                v.x = self.x + x.x
                v.y = self.y + x.y
                v.z = self.z + x.z
                return v
            else:
                raise TypeError("do not know how to add Vector3 and %s"%x.__class__)

        def __radd__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = x + self.x
                v.y = x + self.y
                v.z = x + self.z
                return v
            else:
                raise TypeError("do not know how to add %s and Vector3"%x.__class__)

        def __sub__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = self.x - x
                v.y = self.y - x
                v.z = self.z - x
                return v
            elif isinstance(x, CgfFormat.Vector3):
                v = CgfFormat.Vector3()
                v.x = self.x - x.x
                v.y = self.y - x.y
                v.z = self.z - x.z
                return v
            else:
                raise TypeError("do not know how to substract Vector3 and %s"%x.__class__)

        def __rsub__(self, x):
            if isinstance(x, (float, int, long)):
                v = CgfFormat.Vector3()
                v.x = x - self.x
                v.y = x - self.y
                v.z = x - self.z
                return v
            else:
                raise TypeError("do not know how to substract %s and Vector3"%x.__class__)

        def __neg__(self):
            v = CgfFormat.Vector3()
            v.x = -self.x
            v.y = -self.y
            v.z = -self.z
            return v

        # cross product
        def crossproduct(self, x):
            if isinstance(x, CgfFormat.Vector3):
                v = CgfFormat.Vector3()
                v.x = self.y*x.z - self.z*x.y
                v.y = self.z*x.x - self.x*x.z
                v.z = self.x*x.y - self.y*x.x
                return v
            else:
                raise TypeError("do not know how to calculate crossproduct of Vector3 and %s"%x.__class__)

        def __eq__(self, x):
            if isinstance(x, type(None)):
                return False
            if not isinstance(x, CgfFormat.Vector3):
                raise TypeError("do not know how to compare Vector3 and %s"%x.__class__)
            if abs(self.x - x.x) > CgfFormat.EPSILON: return False
            if abs(self.y - x.y) > CgfFormat.EPSILON: return False
            if abs(self.z - x.z) > CgfFormat.EPSILON: return False
            return True

        def __ne__(self, x):
            return not self.__eq__(x)
