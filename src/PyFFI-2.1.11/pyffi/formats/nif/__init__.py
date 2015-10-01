"""
:mod:`pyffi.formats.nif` --- NetImmerse/Gamebryo (.nif and .kf)
===============================================================

Implementation
--------------

.. autoclass:: NifFormat
   :show-inheritance:
   :members:

Regression tests
----------------

These tests are used to check for functionality and bugs in the library.
They also provide code examples which you may find useful.

Read a NIF file
^^^^^^^^^^^^^^^

>>> stream = open('tests/nif/test.nif', 'rb')
>>> data = NifFormat.Data()
>>> # inspect is optional; it will not read the actual blocks
>>> data.inspect(stream)
>>> hex(data.version)
'0x14010003'
>>> data.user_version
0
>>> for blocktype in data.header.block_types:
...     print(blocktype.decode("ascii"))
NiNode
NiTriShape
NiTriShapeData
>>> data.roots # blocks have not been read yet, so this is an empty list
[]
>>> data.read(stream)
>>> for root in data.roots:
...     for block in root.tree():
...         if isinstance(block, NifFormat.NiNode):
...             print(block.name.decode("ascii"))
test
>>> stream.close()

Parse all NIF files in a directory tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for stream, data in NifFormat.walkData('tests/nif'):
...     try:
...         # the replace call makes the doctest also pass on windows
...         print("reading %s" % stream.name.replace("\\\\", "/"))
...         data.read(stream)
...     except Exception:
...         print(
...             "Warning: read failed due corrupt file,"
...             " corrupt format description, or bug.") # doctest: +REPORT_NDIFF
reading tests/nif/invalid.nif
Warning: read failed due corrupt file, corrupt format description, or bug.
reading tests/nif/nds.nif
reading tests/nif/neosteam.nif
reading tests/nif/test.nif
reading tests/nif/test_centerradius.nif
reading tests/nif/test_check_tangentspace1.nif
reading tests/nif/test_check_tangentspace2.nif
reading tests/nif/test_check_tangentspace3.nif
reading tests/nif/test_check_tangentspace4.nif
reading tests/nif/test_convexverticesshape.nif
reading tests/nif/test_dump_tex.nif
reading tests/nif/test_fix_clampmaterialalpha.nif
reading tests/nif/test_fix_cleanstringpalette.nif
reading tests/nif/test_fix_detachhavoktristripsdata.nif
reading tests/nif/test_fix_disableparallax.nif
reading tests/nif/test_fix_ffvt3rskinpartition.nif
reading tests/nif/test_fix_mergeskeletonroots.nif
reading tests/nif/test_fix_tangentspace.nif
reading tests/nif/test_fix_texturepath.nif
reading tests/nif/test_grid_128x128.nif
reading tests/nif/test_grid_64x64.nif
reading tests/nif/test_mopp.nif
reading tests/nif/test_opt_collision_complex_mopp.nif
reading tests/nif/test_opt_collision_mopp.nif
reading tests/nif/test_opt_collision_packed.nif
reading tests/nif/test_opt_collision_to_boxshape.nif
reading tests/nif/test_opt_collision_to_boxshape_notabox.nif
reading tests/nif/test_opt_collision_unpacked.nif
reading tests/nif/test_opt_delunusedbones.nif
reading tests/nif/test_opt_dupgeomdata.nif
reading tests/nif/test_opt_dupverts.nif
reading tests/nif/test_opt_emptyproperties.nif
reading tests/nif/test_opt_grid_layout.nif
reading tests/nif/test_opt_mergeduplicates.nif
reading tests/nif/test_opt_vertex_cache.nif
reading tests/nif/test_opt_zeroscale.nif
reading tests/nif/test_skincenterradius.nif
reading tests/nif/test_vertexcolor.nif

Create a NIF model from scratch and write to file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> root = NifFormat.NiNode()
>>> root.name = 'Scene Root'
>>> blk = NifFormat.NiNode()
>>> root.add_child(blk)
>>> blk.name = 'new block'
>>> blk.scale = 2.4
>>> blk.translation.x = 3.9
>>> blk.rotation.m_11 = 1.0
>>> blk.rotation.m_22 = 1.0
>>> blk.rotation.m_33 = 1.0
>>> ctrl = NifFormat.NiVisController()
>>> ctrl.flags = 0x000c
>>> ctrl.target = blk
>>> blk.add_controller(ctrl)
>>> blk.add_controller(NifFormat.NiAlphaController())
>>> strips = NifFormat.NiTriStrips()
>>> root.add_child(strips, front = True)
>>> strips.name = "hello world"
>>> strips.rotation.m_11 = 1.0
>>> strips.rotation.m_22 = 1.0
>>> strips.rotation.m_33 = 1.0
>>> data = NifFormat.NiTriStripsData()
>>> strips.data = data
>>> data.num_vertices = 5
>>> data.has_vertices = True
>>> data.vertices.update_size()
>>> for i, v in enumerate(data.vertices):
...     v.x = 1.0+i/10.0
...     v.y = 0.2+1.0/(i+1)
...     v.z = 0.03
>>> data.update_center_radius()
>>> data.num_strips = 2
>>> data.strip_lengths.update_size()
>>> data.strip_lengths[0] = 3
>>> data.strip_lengths[1] = 4
>>> data.has_points = True
>>> data.points.update_size()
>>> data.points[0][0] = 0
>>> data.points[0][1] = 1
>>> data.points[0][2] = 2
>>> data.points[1][0] = 1
>>> data.points[1][1] = 2
>>> data.points[1][2] = 3
>>> data.points[1][3] = 4
>>> data.num_uv_sets = 1
>>> data.has_uv = True
>>> data.uv_sets.update_size()
>>> for i, v in enumerate(data.uv_sets[0]):
...     v.u = 1.0-i/10.0
...     v.v = 1.0/(i+1)
>>> data.has_normals = True
>>> data.normals.update_size()
>>> for i, v in enumerate(data.normals):
...     v.x = 0.0
...     v.y = 0.0
...     v.z = 1.0
>>> strips.update_tangent_space()
>>> from tempfile import TemporaryFile
>>> stream = TemporaryFile()
>>> nifdata = NifFormat.Data(version=0x14010003, user_version=10)
>>> nifdata.roots = [root]
>>> nifdata.write(stream)
>>> stream.close()

Get list of versions and games
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> for vnum in sorted(NifFormat.versions.values()):
...     print('0x%08X' % vnum) # doctest: +REPORT_UDIFF
0x02030000
0x03000000
0x03000300
0x03010000
0x0303000D
0x04000000
0x04000002
0x0401000C
0x04020002
0x04020100
0x04020200
0x0A000100
0x0A000102
0x0A000103
0x0A010000
0x0A010065
0x0A01006A
0x0A020000
0x0A020001
0x0A040001
0x14000004
0x14000005
0x14010003
0x14020007
0x14020008
0x14030001
0x14030002
0x14030003
0x14030006
0x14030009
0x14050000
0x14060000
0x14060500
0x1E000002
>>> for game, versions in sorted(NifFormat.games.items(), key=lambda x: x[0]):
...     print("%s " % game + " ".join('0x%08X' % vnum for vnum in versions)) # doctest: +REPORT_UDIFF
? 0x0A000103
Atlantica 0x14020008
Axis and Allies 0x0A010000
Bully SE 0x14030009
Civilization IV 0x04020002 0x04020100 0x04020200 0x0A000100 0x0A010000 \
0x0A020000 0x14000004
Culpa Innata 0x04020200
Dark Age of Camelot 0x02030000 0x03000300 0x03010000 0x0401000C 0x04020100 \
0x04020200 0x0A010000
Divinity 2 0x14030009
Emerge 0x14020007 0x14020008 0x14030001 0x14030002 0x14030003 0x14030006 \
0x1E000002
Empire Earth II 0x04020200 0x0A010000
Empire Earth III 0x14020007 0x14020008
Entropia Universe 0x0A010000
Epic Mickey 0x14060500
Fallout 3 0x14020007
Freedom Force 0x04000000 0x04000002
Freedom Force vs. the 3rd Reich 0x0A010000
Howling Sword 0x14030009
Kohan 2 0x0A010000
KrazyRain 0x14050000 0x14060000
Lazeska 0x14030009
Loki 0x0A020000
Megami Tensei: Imagine 0x14010003
Morrowind 0x04000002
NeoSteam 0x0A010000
Oblivion 0x0303000D 0x0A000100 0x0A000102 0x0A010065 0x0A01006A 0x0A020000 0x14000004 \
0x14000005
Prison Tycoon 0x0A020000
Pro Cycling Manager 0x0A020000
Red Ocean 0x0A020000
Sid Meier's Railroads 0x14000004
Star Trek: Bridge Commander 0x03000000 0x03010000
The Guild 2 0x0A010000
Warhammer 0x14030009
Wildlife Park 2 0x0A010000 0x0A020000
Worldshift 0x0A020001 0x0A040001
Zoo Tycoon 2 0x0A000100

Reading an unsupported nif file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

>>> stream = open('tests/nif/invalid.nif', 'rb')
>>> data = NifFormat.Data()
>>> data.inspect(stream) # the file seems ok on inspection
>>> data.read(stream) # doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
ValueError: ...
>>> stream.close()

Template types
^^^^^^^^^^^^^^

>>> block = NifFormat.NiTextKeyExtraData()
>>> block.num_text_keys = 1
>>> block.text_keys.update_size()
>>> block.text_keys[0].time = 1.0
>>> block.text_keys[0].value = 'hi'

Links
^^^^^

>>> NifFormat.NiNode._has_links
True
>>> NifFormat.NiBone._has_links
True
>>> skelroot = NifFormat.NiNode()
>>> geom = NifFormat.NiTriShape()
>>> geom.skin_instance = NifFormat.NiSkinInstance()
>>> geom.skin_instance.skeleton_root = skelroot
>>> [block.__class__.__name__ for block in geom.get_refs()]
['NiSkinInstance']
>>> [block.__class__.__name__ for block in geom.get_links()]
['NiSkinInstance']
>>> [block.__class__.__name__ for block in geom.skin_instance.get_refs()]
[]
>>> [block.__class__.__name__ for block in geom.skin_instance.get_links()]
['NiNode']

Strings
^^^^^^^

>>> extra = NifFormat.NiTextKeyExtraData()
>>> extra.num_text_keys = 2
>>> extra.text_keys.update_size()
>>> extra.text_keys[0].time = 0.0
>>> extra.text_keys[0].value = "start"
>>> extra.text_keys[1].time = 2.0
>>> extra.text_keys[1].value = "end"
>>> for extrastr in extra.get_strings(None):
...     print(extrastr.decode("ascii"))
start
end
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

from itertools import izip, repeat, chain
import logging
import math # math.pi
import os
import re
import struct
import sys
import warnings
import weakref

import pyffi.formats.bsa
import pyffi.formats.dds
import pyffi.object_models.common
import pyffi.object_models
from pyffi.object_models.xml import FileFormat
import pyffi.utils.inertia
from pyffi.utils.mathutils import * # XXX todo get rid of from XXX import *
import pyffi.utils.mopp
import pyffi.utils.tristrip
import pyffi.utils.vertex_cache
import pyffi.utils.quickhull
# XXX convert the following to absolute imports
from pyffi.object_models.editable import EditableBoolComboBox
from pyffi.utils.graph import EdgeFilter
from pyffi.object_models.xml.basic import BasicBase
from pyffi.object_models.xml.struct_ import StructBase



class NifFormat(FileFormat):
    """This class contains the generated classes from the xml."""
    xml_file_name = 'nif.xml'
    # where to look for nif.xml and in what order: NIFXMLPATH env var,
    # or NifFormat module directory
    xml_file_path = [os.getenv('NIFXMLPATH'),
                     os.path.join(os.path.dirname(__file__), "nifxml")]
    # filter for recognizing nif files by extension
    # .kf are nif files containing keyframes
    # .kfa are nif files containing keyframes in DAoC style
    # .nifcache are Empire Earth II nif files
    # .texcache are Empire Earth II/III packed texture nif files
    # .pcpatch are Empire Earth II/III packed texture nif files
    # .item are Divinity 2 nif files
    # .nft are Bully SE nif files (containing textures)
    # .nif_wii are Epic Mickey nif files
    RE_FILENAME = re.compile(r'^.*\.(nif|kf|kfa|nifcache|jmi|texcache|pcpatch|nft|item|nif_wii)$', re.IGNORECASE)
    # archives
    ARCHIVE_CLASSES = [pyffi.formats.bsa.BsaFormat]
    # used for comparing floats
    EPSILON = 0.0001

    # basic types
    ulittle32 = pyffi.object_models.common.ULittle32
    int = pyffi.object_models.common.Int
    uint = pyffi.object_models.common.UInt
    byte = pyffi.object_models.common.UByte # not a typo
    char = pyffi.object_models.common.Char
    short = pyffi.object_models.common.Short
    ushort = pyffi.object_models.common.UShort
    float = pyffi.object_models.common.Float
    BlockTypeIndex = pyffi.object_models.common.UShort
    StringIndex = pyffi.object_models.common.UInt
    SizedString = pyffi.object_models.common.SizedString

    # implementation of nif-specific basic types

    class StringOffset(pyffi.object_models.common.Int):
        """This is just an integer with -1 as default value."""
        def __init__(self, **kwargs):
            pyffi.object_models.common.Int.__init__(self, **kwargs)
            self.set_value(-1)

    class bool(BasicBase, EditableBoolComboBox):
        """Basic implementation of a 32-bit (8-bit for versions > 4.0.0.2)
        boolean type.

        >>> i = NifFormat.bool()
        >>> i.set_value('false')
        >>> i.get_value()
        False
        >>> i.set_value('true')
        >>> i.get_value()
        True
        """
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self.set_value(False)

        def get_value(self):
            return self._value

        def set_value(self, value):
            if isinstance(value, basestring):
                if value.lower() == 'false':
                    self._value = False
                    return
                elif value == '0':
                    self._value = False
                    return
            if value:
                self._value = True
            else:
                self._value = False

        def get_size(self, data=None):
            ver = data.version if data else -1
            if ver > 0x04000002:
                return 1
            else:
                return 4

        def get_hash(self, data=None):
            return self._value

        def read(self, stream, data):
            if data.version > 0x04000002:
                value, = struct.unpack(data._byte_order + 'B',
                                       stream.read(1))
            else:
                value, = struct.unpack(data._byte_order + 'I',
                                       stream.read(4))
            self._value = bool(value)

        def write(self, stream, data):
            if data.version > 0x04000002:
                stream.write(struct.pack(data._byte_order + 'B',
                                         int(self._value)))
            else:
                stream.write(struct.pack(data._byte_order + 'I',
                                         int(self._value)))

    class Flags(pyffi.object_models.common.UShort):
        def __str__(self):
            return hex(self.get_value())

    class Ref(BasicBase):
        """Reference to another block."""
        _is_template = True
        _has_links = True
        _has_refs = True
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self._template = kwargs.get("template")
            self.set_value(None)

        def get_value(self):
            return self._value

        def set_value(self, value):
            if value is None:
                self._value = None
            else:
                if not isinstance(value, self._template):
                    raise TypeError(
                        'expected an instance of %s but got instance of %s'
                        % (self._template, value.__class__))
                self._value = value

        def get_size(self, data=None):
            return 4

        def get_hash(self, data=None):
            if self.get_value():
                return self.get_value().get_hash(data)
            else:
                return None

        def read(self, stream, data):
            self.set_value(None) # fix_links will set this field
            block_index, = struct.unpack(data._byte_order + 'i',
                                         stream.read(4))
            data._link_stack.append(block_index)

        def write(self, stream, data):
            """Write block reference."""
            if self.get_value() is None:
                # -1: link by number, 0: link by pointer
                block_index = -1 if data.version >= 0x0303000D else 0
            else:
                try:
                    block_index = data._block_index_dct[self.get_value()]
                except KeyError:
                    logging.getLogger("pyffi.nif.ref").warn(
                        "%s block is missing from the nif tree:"
                        " omitting reference"
                        % self.get_value().__class__.__name__)
                    # -1: link by number, 0: link by pointer
                    block_index = -1 if data.version >= 0x0303000D else 0
            stream.write(struct.pack(
                data._byte_order + 'i', block_index))

        def fix_links(self, data):
            """Fix block links."""
            block_index = data._link_stack.pop(0)
            # case when there's no link
            if data.version >= 0x0303000D:
                if block_index == -1: # link by block number
                    self.set_value(None)
                    return
            else:
                if block_index == 0: # link by pointer
                    self.set_value(None)
                    return
            # other case: look up the link and check the link type
            block = data._block_dct[block_index]
            if isinstance(block, self._template):
                self.set_value(block)
            else:
                #raise TypeError('expected an instance of %s but got instance of %s'%(self._template, block.__class__))
                logging.getLogger("pyffi.nif.ref").warn(
                    "Expected an %s but got %s: ignoring reference."
                    % (self._template, block.__class__))

        def get_links(self, data=None):
            val = self.get_value()
            if val is not None:
                return [val]
            else:
                return []

        def get_refs(self, data=None):
            val = self.get_value()
            if val is not None:
                return [val]
            else:
                return []

        def replace_global_node(self, oldbranch, newbranch,
                                edge_filter=EdgeFilter()):
            """
            >>> from pyffi.formats.nif import NifFormat
            >>> x = NifFormat.NiNode()
            >>> y = NifFormat.NiNode()
            >>> z = NifFormat.NiNode()
            >>> x.add_child(y)
            >>> x.children[0] is y
            True
            >>> x.children[0] is z
            False
            >>> x.replace_global_node(y, z)
            >>> x.children[0] is y
            False
            >>> x.children[0] is z
            True
            >>> x.replace_global_node(z, None)
            >>> x.children[0] is None
            True
            """
            if self.get_value() is oldbranch:
                # set_value takes care of template type
                self.set_value(newbranch)
                #print("replacing", repr(oldbranch), "->", repr(newbranch))
            if self.get_value() is not None:
                self.get_value().replace_global_node(oldbranch, newbranch)

        def get_detail_display(self):
            # return the node itself, if it is not None
            if self.get_value() is not None:
                return self.get_value()
            else:
                return "None"

    class Ptr(Ref):
        """A weak reference to another block, used to point up the hierarchy tree. The reference is not returned by the L{get_refs} function to avoid infinite recursion."""
        _is_template = True
        _has_links = True
        _has_refs = False

        # use weak reference to aid garbage collection

        def get_value(self):
            return self._value() if self._value is not None else None

        def set_value(self, value):
            if value is None:
                self._value = None
            else:
                if not isinstance(value, self._template):
                    raise TypeError(
                        'expected an instance of %s but got instance of %s'
                        % (self._template, value.__class__))
                self._value = weakref.ref(value)

        def __str__(self):
            # avoid infinite recursion
            return '%s instance at 0x%08X'%(self._value.__class__, id(self._value))

        def get_refs(self, data=None):
            return []

        def get_hash(self, data=None):
            return None

        def replace_global_node(self, oldbranch, newbranch,
                              edge_filter=EdgeFilter()):
            # overridden to avoid infinite recursion
            if self.get_value() is oldbranch:
                self.set_value(newbranch)
                #print("replacing", repr(oldbranch), "->", repr(newbranch))

    class LineString(BasicBase):
        """Basic type for strings ending in a newline character (0x0a).

        >>> from tempfile import TemporaryFile
        >>> f = TemporaryFile()
        >>> l = NifFormat.LineString()
        >>> f.write('abcdefg\\x0a'.encode())
        >>> f.seek(0)
        >>> l.read(f)
        >>> str(l)
        'abcdefg'
        >>> f.seek(0)
        >>> l.set_value('Hi There')
        >>> l.write(f)
        >>> f.seek(0)
        >>> m = NifFormat.LineString()
        >>> m.read(f)
        >>> str(m)
        'Hi There'
        """
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self.set_value('')

        def get_value(self):
            return self._value

        def set_value(self, value):
            self._value = pyffi.object_models.common._as_bytes(value).rstrip('\x0a'.encode("ascii"))

        def __str__(self):
            return pyffi.object_models.common._as_str(self._value)

        def get_size(self, data=None):
            return len(self._value) + 1 # +1 for trailing endline

        def get_hash(self, data=None):
            return self.get_value()

        def read(self, stream, data=None):
            self._value = stream.readline().rstrip('\x0a'.encode("ascii"))

        def write(self, stream, data=None):
            stream.write(self._value)
            stream.write("\x0a".encode("ascii"))

    class HeaderString(BasicBase):
        def __str__(self):
            return 'NetImmerse/Gamebryo File Format, Version x.x.x.x'

        def get_detail_display(self):
            return self.__str__()

        def get_hash(self, data=None):
            return None

        def read(self, stream, data):
            version_string = self.version_string(data.version, data.modification)
            s = stream.read(len(version_string))
            if s != version_string.encode("ascii"):
                raise ValueError(
                    "invalid NIF header: expected '%s' but got '%s'"
                    % (version_string, s))
            # for almost all nifs we have version_string + \x0a
            # but Bully SE has some nifs with version_string + \x0d\x0a
            # see for example World/BBonusB.nft
            eol = stream.read(1)
            if eol == '\x0d'.encode("ascii"):
                eol = stream.read(1)
            if eol != '\x0a'.encode("ascii"):
                raise ValueError(
                    "invalid NIF header: bad version string eol")

        def write(self, stream, data):
            stream.write(self.version_string(data.version, data.modification).encode("ascii"))
            stream.write('\x0a'.encode("ascii"))

        def get_size(self, data=None):
            ver = data.version if data else -1
            return len(self.version_string(ver).encode("ascii")) + 1

        @staticmethod
        def version_string(version, modification=None):
            """Transforms version number into a version string.

            >>> NifFormat.HeaderString.version_string(0x03000300)
            'NetImmerse File Format, Version 3.03'
            >>> NifFormat.HeaderString.version_string(0x03010000)
            'NetImmerse File Format, Version 3.1'
            >>> NifFormat.HeaderString.version_string(0x0A000100)
            'NetImmerse File Format, Version 10.0.1.0'
            >>> NifFormat.HeaderString.version_string(0x0A010000)
            'Gamebryo File Format, Version 10.1.0.0'
            >>> NifFormat.HeaderString.version_string(0x0A010000,
            ...                                       modification="neosteam")
            'NS'
            >>> NifFormat.HeaderString.version_string(0x14020008,
            ...                                       modification="ndoors")
            'NDSNIF....@....@...., Version 20.2.0.8'
            >>> NifFormat.HeaderString.version_string(0x14030009,
            ...                                       modification="jmihs1")
            'Joymaster HS1 Object Format - (JMI), Version 20.3.0.9'
            """
            if version == -1 or version is None:
                raise ValueError('No string for version %s.'%version)
            if modification == "neosteam":
                if version != 0x0A010000:
                    raise ValueError("NeoSteam must have version 0x0A010000.")
                return "NS"
            elif version <= 0x0A000102:
                s = "NetImmerse"
            else:
                s = "Gamebryo"
            if version == 0x03000300:
                v = "3.03"
            elif version <= 0x03010000:
                v = "%i.%i"%((version >> 24) & 0xff, (version >> 16) & 0xff)
            else:
                v = "%i.%i.%i.%i"%((version >> 24) & 0xff, (version >> 16) & 0xff, (version >> 8) & 0xff, version & 0xff)
            if modification == "ndoors":
                return "NDSNIF....@....@...., Version %s" % v
            elif modification == "jmihs1":
                return "Joymaster HS1 Object Format - (JMI), Version %s" % v
            else:
                return "%s File Format, Version %s" % (s, v)

    class FileVersion(BasicBase):
        def get_value(self):
            raise NotImplementedError

        def set_value(self, value):
            raise NotImplementedError

        def __str__(self):
            return 'x.x.x.x'

        def get_size(self, data=None):
            return 4

        def get_hash(self, data=None):
            return None

        def read(self, stream, data):
            modification = data.modification
            ver, = struct.unpack('<I', stream.read(4)) # always little endian
            if (not modification) or modification == "jmihs1":
                if ver != data.version:
                    raise ValueError(
                        "Invalid version number: "
                        "expected 0x%08X but got 0x%08X."
                        % (data.version, ver))
            elif modification == "neosteam":
                if ver != 0x08F35232:
                    raise ValueError(
                        "Invalid NeoSteam version number: "
                        "expected 0x%08X but got 0x%08X."
                        % (0x08F35232, ver))
            elif modification == "ndoors":
                if ver != 0x73615F67:
                    raise ValueError(
                        "Invalid Ndoors version number: "
                        "expected 0x%08X but got 0x%08X."
                        % (0x73615F67, ver))
            elif modification == "laxelore":
                if ver != 0x5A000004:
                    raise ValueError(
                        "Invalid Laxe Lore version number: "
                        "expected 0x%08X but got 0x%08X."
                        % (0x5A000004, ver))
            else:
                raise ValueError(
                    "unknown modification: '%s'" % modification)

        def write(self, stream, data):
            # always little endian
            modification = data.modification
            if (not modification) or modification == "jmihs1":
                stream.write(struct.pack('<I', data.version))
            elif modification == "neosteam":
                stream.write(struct.pack('<I', 0x08F35232))
            elif modification == "ndoors":
                stream.write(struct.pack('<I', 0x73615F67))
            elif modification == "laxelore":
                stream.write(struct.pack('<I', 0x5A000004))
            else:
                raise ValueError(
                    "unknown modification: '%s'" % modification)

        def get_detail_display(self):
            return 'x.x.x.x'

    class ShortString(BasicBase):
        """Another type for strings."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self._value = ''.encode("ascii")

        def get_value(self):
            return self._value

        def set_value(self, value):
            val = pyffi.object_models.common._as_bytes(value)
            if len(val) > 254:
                raise ValueError('string too long')
            self._value = val

        def __str__(self):
            return pyffi.object_models.common._as_str(self._value)

        def get_size(self, data=None):
            # length byte + string chars + zero byte
            return len(self._value) + 2

        def get_hash(self, data=None):
            return self.get_value()

        def read(self, stream, data):
            n, = struct.unpack(data._byte_order + 'B',
                               stream.read(1))
            self._value = stream.read(n).rstrip('\x00'.encode("ascii"))

        def write(self, stream, data):
            stream.write(struct.pack(data._byte_order + 'B',
                                     len(self._value)+1))
            stream.write(self._value)
            stream.write('\x00'.encode("ascii"))

    class string(SizedString):
        _has_strings = True

        def get_size(self, data=None):
            ver = data.version if data else -1
            if ver >= 0x14010003:
                return 4
            else:
                return 4 + len(self._value)

        def read(self, stream, data):
            n, = struct.unpack(data._byte_order + 'i', stream.read(4))
            if data.version >= 0x14010003:
                if n == -1:
                    self._value = ''.encode("ascii")
                else:
                    try:
                        self._value = data._string_list[n]
                    except IndexError:
                        raise ValueError('string index too large (%i)'%n)
            else:
                if n > 10000:
                    raise ValueError('string too long (0x%08X at 0x%08X)'
                                     % (n, stream.tell()))
                self._value = stream.read(n)

        def write(self, stream, data):
            if data.version >= 0x14010003:
                if not self._value:
                    stream.write(
                        struct.pack(data._byte_order + 'i', -1))
                else:
                    try:
                        stream.write(struct.pack(
                            data._byte_order + 'i',
                            data._string_list.index(self._value)))
                    except ValueError:
                        raise ValueError(
                            "string '%s' not in string list" % self._value)
            else:
                stream.write(struct.pack(data._byte_order + 'I',
                                         len(self._value)))
                stream.write(self._value)

        def get_strings(self, data):
            if self._value:
                return [self._value]
            else:
                return []

        def get_hash(self, data=None):
            return self.get_value()

    # other types with internal implementation

    class FilePath(string):
        """A file path."""
        def get_hash(self, data=None):
            """Returns a case insensitive hash value."""
            return self.get_value().lower()

    class ByteArray(BasicBase):
        """Array (list) of bytes. Implemented as basic type to speed up reading
        and also to prevent data to be dumped by __str__."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self.set_value("".encode()) # b'' for > py25

        def get_value(self):
            return self._value

        def set_value(self, value):
            self._value = pyffi.object_models.common._as_bytes(value)

        def get_size(self, data=None):
            return len(self._value) + 4

        def get_hash(self, data=None):
            return self._value.__hash__()

        def read(self, stream, data):
            size, = struct.unpack(data._byte_order + 'I',
                                  stream.read(4))
            self._value = stream.read(size)

        def write(self, stream, data):
            stream.write(struct.pack(data._byte_order + 'I',
                                     len(self._value)))
            stream.write(self._value)

        def __str__(self):
            return "< %i Bytes >" % len(self._value)

    class ByteMatrix(BasicBase):
        """Matrix of bytes. Implemented as basic type to speed up reading
        and to prevent data being dumped by __str__."""
        def __init__(self, **kwargs):
            BasicBase.__init__(self, **kwargs)
            self.set_value([])

        def get_value(self):
            return self._value

        def set_value(self, value):
            assert(isinstance(value, list))
            if value:
                size1 = len(value[0])
            for x in value:
                # TODO fix this for py3k
                #assert(isinstance(x, basestring))
                assert(len(x) == size1)
            self._value = value # should be a list of strings of bytes

        def get_size(self, data=None):
            if len(self._value) == 0:
                return 8
            else:
                return len(self._value) * len(self._value[0]) + 8

        def get_hash(self, data=None):
            return tuple( x.__hash__() for x in self._value )

        def read(self, stream, data):
            size1, = struct.unpack(data._byte_order + 'I',
                                   stream.read(4))
            size2, = struct.unpack(data._byte_order + 'I',
                                   stream.read(4))
            self._value = []
            for i in xrange(size2):
                self._value.append(stream.read(size1))

        def write(self, stream, data):
            if self._value:
                stream.write(struct.pack(data._byte_order + 'I',
                                         len(self._value[0])))
            else:
                stream.write(struct.pack(data._byte_order + 'I', 0))
            stream.write(struct.pack(data._byte_order + 'I',
                                     len(self._value)))
            for x in self._value:
                stream.write(x)

        def __str__(self):
            size1 = len(self._value[0]) if self._value else 0
            size2 = len(self._value)
            return "< %ix%i Bytes >" % (size2, size1)

    @classmethod
    def vercondFilter(cls, expression):
        if expression == "Version":
            return "version"
        elif expression == "User Version":
            return "user_version"
        elif expression == "User Version 2":
            return "user_version2"
        ver = cls.version_number(expression)
        if ver < 0:
            # not supported?
            raise ValueError(
                "cannot recognize version expression '%s'" % expression)
        else:
            return ver

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.

        :param version_str: The version string.
        :type version_str: str
        :return: A version integer.

        >>> hex(NifFormat.version_number('3.14.15.29'))
        '0x30e0f1d'
        >>> hex(NifFormat.version_number('1.2'))
        '0x1020000'
        >>> hex(NifFormat.version_number('3.03'))
        '0x3000300'
        >>> hex(NifFormat.version_number('NS'))
        '0xa010000'
        """

        # 3.03 case is special
        if version_str == '3.03':
            return 0x03000300

        # NS (neosteam) case is special
        if version_str == 'NS':
            return 0x0A010000

        try:
            ver_list = [int(x) for x in version_str.split('.')]
        except ValueError:
            return -1 # version not supported (i.e. version_str '10.0.1.3a' would trigger this)
        if len(ver_list) > 4 or len(ver_list) < 1:
            return -1 # version not supported
        for ver_digit in ver_list:
            if (ver_digit | 0xff) > 0xff:
                return -1 # version not supported
        while len(ver_list) < 4: ver_list.append(0)
        return (ver_list[0] << 24) + (ver_list[1] << 16) + (ver_list[2] << 8) + ver_list[3]

    # exceptions
    class NifError(Exception):
        """Standard nif exception class."""
        pass

    class Data(pyffi.object_models.FileFormat.Data):
        """A class to contain the actual nif data.

        Note that L{header} and L{blocks} are not automatically kept
        in sync with the rest of the nif data, but they are
        resynchronized when calling L{write}.

        :ivar version: The nif version.
        :type version: ``int``
        :ivar user_version: The nif user version.
        :type user_version: ``int``
        :ivar user_version2: The nif user version 2.
        :type user_version2: ``int``
        :ivar roots: List of root blocks.
        :type roots: ``list`` of L{NifFormat.NiObject}
        :ivar header: The nif header.
        :type header: L{NifFormat.Header}
        :ivar blocks: List of blocks.
        :type blocks: ``list`` of L{NifFormat.NiObject}
        :ivar modification: Neo Steam ("neosteam") or Ndoors ("ndoors") or Joymaster Interactive Howling Sword ("jmihs1") or Laxe Lore ("laxelore") style nif?
        :type modification: ``str``
        """

        _link_stack = None
        _block_dct = None
        _string_list = None
        _block_index_dct = None

        class VersionUInt(pyffi.object_models.common.UInt):
            def set_value(self, value):
                if value is None:
                    self._value = None
                else:
                    pyffi.object_models.common.UInt.set_value(self, value)

            def __str__(self):
                if self._value is None:
                    return "None"
                else:
                    return "0x%08X" % self.get_value()

            def get_detail_display(self):
                return self.__str__()

        def __init__(self, version=0x04000002, user_version=0, user_version2=0):
            """Initialize nif data. By default, this creates an empty
            nif document of the given version and user version.

            :param version: The version.
            :type version: ``int``
            :param user_version: The user version.
            :type user_version: ``int``
            """
            # the version numbers are stored outside the header structure
            self._version_value_ = self.VersionUInt()
            self._version_value_.set_value(version)
            self._user_version_value_ = self.VersionUInt()
            self._user_version_value_.set_value(user_version)
            self._user_version_2_value_ = self.VersionUInt()
            self._user_version_2_value_.set_value(user_version2)
            # create new header
            self.header = NifFormat.Header()
            # empty list of root blocks (this encodes the footer)
            self.roots = []
            # empty list of blocks
            self.blocks = []
            # not a neosteam or ndoors nif
            self.modification = None

        def _getVersion(self):
            return self._version_value_.get_value()
        def _setVersion(self, value):
            self._version_value_.set_value(value)
            
        def _getUserVersion(self):
            return self._user_version_value_.get_value()
        def _setUserVersion(self, value):
            self._user_version_value_.set_value(value)

        def _getUserVersion2(self):
            return self._user_version_2_value_.get_value()
        def _setUserVersion2(self, value):
            self._user_version_2_value_.set_value(value)

        version = property(_getVersion, _setVersion)
        user_version = property(_getUserVersion, _setUserVersion)
        user_version2 = property(_getUserVersion2, _setUserVersion2)

        # new functions

        def inspect_version_only(self, stream):
            """This function checks the version only, and is faster
            than the usual inspect function (which reads the full
            header). Sets the L{version} and L{user_version} instance
            variables if the stream contains a valid nif file.

            Call this function if you simply wish to check that a file is
            a nif file without having to parse even the header.

            :raise ``ValueError``: If the stream does not contain a nif file.
            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            pos = stream.tell()
            try:
                s = stream.readline(64).rstrip()
            finally:
                stream.seek(pos)
            self.modification = None
            if s.startswith("NetImmerse File Format, Version ".encode("ascii")):
                version_str = s[32:].decode("ascii")
            elif s.startswith("Gamebryo File Format, Version ".encode("ascii")):
                version_str = s[30:].decode("ascii")
            elif s.startswith("NS".encode("ascii")):
                # neosteam
                version_str = "NS"
                self.modification = "neosteam"
            elif s.startswith("NDSNIF....@....@...., Version ".encode("ascii")):
                version_str = s[30:].decode("ascii")
                self.modification = "ndoors"
            elif s.startswith("Joymaster HS1 Object Format - (JMI), Version ".encode("ascii")):
                version_str = s[45:].decode("ascii")
                self.modification = "jmihs1"
            else:
                raise ValueError("Not a nif file.")
            try:
                ver = NifFormat.version_number(version_str)
            except:
                raise ValueError("Nif version %s not supported." % version_str)
            if not ver in NifFormat.versions.values():
                raise ValueError("Nif version %s not supported." % version_str)
            # check version integer and user version
            userver = 0
            userver2 = 0
            if ver >= 0x0303000D:
                ver_int = None
                try:
                    stream.readline(64)
                    ver_int, = struct.unpack('<I', stream.read(4))
                    # special case for Laxe Lore
                    if ver_int == 0x5A000004 and ver == 0x14000004:
                        self.modification = "laxelore"
                    # neosteam and ndoors have a special version integer
                    elif (not self.modification) or self.modification == "jmihs1":
                        if ver_int != ver:
                            raise ValueError(
                                "Corrupted nif file: header version string %s"
                                " does not correspond with header version field"
                                " 0x%08X." % (version_str, ver_int))
                    elif self.modification == "neosteam":
                        if ver_int != 0x08F35232:
                            raise ValueError(
                                "Corrupted nif file: invalid NeoSteam version.")
                    elif self.modification == "ndoors":
                        if ver_int != 0x73615F67:
                            raise ValueError(
                                "Corrupted nif file: invalid Ndoors version.")
                    if ver >= 0x14000004:
                        endian_type, = struct.unpack('<B', stream.read(1))
                        if endian_type == 0:
                            # big endian!
                            self._byte_order = '>'
                    if ver >= 0x0A010000:
                        userver, = struct.unpack('<I', stream.read(4))
                        if userver in (10, 11):
                            stream.read(4) # number of blocks
                            userver2, = struct.unpack('<I', stream.read(4))
                finally:
                    stream.seek(pos)
            self.version = ver
            self.user_version = userver
            self.user_version2 = userver2

        # GlobalNode

        def get_global_child_nodes(self, edge_filter=EdgeFilter()):
            return (root for root in self.roots)

        # DetailNode

        def replace_global_node(self, oldbranch, newbranch,
                              edge_filter=EdgeFilter()):
            for i, root in enumerate(self.roots):
                if root is oldbranch:
                    self.roots[i] = newbranch
                else:
                    root.replace_global_node(oldbranch, newbranch,
                                           edge_filter=edge_filter)

        def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
            yield self._version_value_
            yield self._user_version_value_
            yield self._user_version_2_value_
            yield self.header

        def get_detail_child_names(self, edge_filter=EdgeFilter()):
            yield "Version"
            yield "User Version"
            yield "User Version 2"
            yield "Header"

        # overriding pyffi.object_models.FileFormat.Data methods

        def inspect(self, stream):
            """Quickly checks whether the stream appears to contain
            nif data, and read the nif header. Resets stream to original position.

            Call this function if you only need to inspect the header of the nif.

            :param stream: The file to inspect.
            :type stream: ``file``
            """
            pos = stream.tell()
            try:
                self.inspect_version_only(stream)
                self.header.read(stream, data=self)
            finally:
                stream.seek(pos)

        def read(self, stream):
            """Read a nif file. Does not reset stream position.

            :param stream: The stream from which to read.
            :type stream: ``file``
            """
            logger = logging.getLogger("pyffi.nif.data")
            # read header
            logger.debug("Reading header at 0x%08X" % stream.tell())
            self.inspect_version_only(stream)
            logger.debug("Version 0x%08X" % self.version)
            self.header.read(stream, data=self)

            # list of root blocks
            # for versions < 3.3.0.13 this list is updated through the
            # "Top Level Object" string while reading the blocks
            # for more recent versions, this list is updated at the end when the
            # footer is read
            self.roots = []

            # read the blocks
            self._link_stack = [] # list of indices, as they are added to the stack
            self._string_list = [s for s in self.header.strings]
            self._block_dct = {} # maps block index to actual block
            self.blocks = [] # records all blocks as read from file in order
            block_num = 0 # the current block numner

            while True:
                if self.version < 0x0303000D:
                    # check if this is a 'Top Level Object'
                    pos = stream.tell()
                    top_level_str = NifFormat.SizedString()
                    top_level_str.read(stream, data=self)
                    top_level_str = str(top_level_str)
                    if top_level_str == "Top Level Object":
                        is_root = True
                    else:
                        is_root = False
                        stream.seek(pos)
                else:
                    # signal as no root for now, roots are added when the footer
                    # is read
                    is_root = False

                # get block name
                if self.version >= 0x05000001:
                    # note the 0xfff mask: required for the NiPhysX blocks
                    block_type = self.header.block_types[
                        self.header.block_type_index[block_num] & 0xfff]
                    block_type = block_type.decode("ascii")
                    # handle data stream classes
                    if block_type.startswith("NiDataStream\x01"):
                        block_type, data_stream_usage, data_stream_access = block_type.split("\x01")
                        data_stream_usage = int(data_stream_usage)
                        data_stream_access = int(data_stream_access)
                    # read dummy integer
                    # bhk blocks are *not* preceeded by a dummy
                    if self.version <= 0x0A01006A and not block_type.startswith("bhk"):
                        dummy, = struct.unpack(self._byte_order + 'I',
                                               stream.read(4))
                        if dummy != 0:
                            raise NifFormat.NifError(
                                'non-zero block tag 0x%08X at 0x%08X)'
                                %(dummy, stream.tell()))
                else:
                    block_type = NifFormat.SizedString()
                    block_type.read(stream, self)
                    block_type = block_type.get_value().decode("ascii")
                # get the block index
                if self.version >= 0x0303000D:
                    # for these versions the block index is simply the block number
                    block_index = block_num
                else:
                    # earlier versions
                    # the number of blocks is not in the header
                    # and a special block type string marks the end of the file
                    if block_type == "End Of File": break
                    # read the block index, which is probably the memory
                    # location of the object when it was written to
                    # memory
                    else:
                        block_index, = struct.unpack(
                            self._byte_order + 'I', stream.read(4))
                        if block_index in self._block_dct:
                            raise NifFormat.NifError(
                                'duplicate block index (0x%08X at 0x%08X)'
                                %(block_index, stream.tell()))
                # create the block
                try:
                    block = getattr(NifFormat, block_type)()
                except AttributeError:
                    raise ValueError(
                        "Unknown block type '%s'." % block_type)
                logger.debug("Reading %s block at 0x%08X"
                             % (block_type, stream.tell()))
                # read the block
                try:
                    block.read(stream, self)
                except:
                    logger.exception("Reading %s failed" % block.__class__)
                    #logger.error("link stack: %s" % self._link_stack)
                    #logger.error("block that failed:")
                    #logger.error("%s" % block)
                    raise
                # complete NiDataStream data
                if block_type == "NiDataStream":
                    block.usage = data_stream_usage
                    block.access.from_int(data_stream_access, self)
                # store block index
                self._block_dct[block_index] = block
                self.blocks.append(block)
                # check block size
                if self.version >= 0x14020007:
                    logger.debug("Checking block size")
                    calculated_size = block.get_size(data=self)
                    if calculated_size != self.header.block_size[block_num]:
                        extra_size = self.header.block_size[block_num] - calculated_size
                        logger.error(
                            "Block size check failed: corrupt nif file "
                            "or bad nif.xml?")
                        logger.error("Skipping %i bytes in %s"
                                     % (extra_size, block.__class__.__name__))
                        # skip bytes that were missed
                        stream.seek(extra_size, 1)
                # add block to roots if flagged as such
                if is_root:
                    self.roots.append(block)
                # check if we are done
                block_num += 1
                if self.version >= 0x0303000D:
                    if block_num >= self.header.num_blocks:
                        break

            # read footer
            ftr = NifFormat.Footer()
            ftr.read(stream, self)

            # check if we are at the end of the file
            if stream.read(1):
                logger.error(
                    'End of file not reached: corrupt nif file?')

            # fix links in blocks and footer (header has no links)
            for block in self.blocks:
                block.fix_links(self)
            ftr.fix_links(self)
            # the link stack should be empty now
            if self._link_stack:
                raise NifFormat.NifError('not all links have been popped from the stack (bug?)')
            # add root objects in footer to roots list
            if self.version >= 0x0303000D:
                for root in ftr.roots:
                    self.roots.append(root)

        def write(self, stream):
            """Write a nif file. The L{header} and the L{blocks} are recalculated
            from the tree at L{roots} (e.g. list of block types, number of blocks,
            list of block types, list of strings, list of block sizes etc.).

            :param stream: The stream to which to write.
            :type stream: file
            """
            logger = logging.getLogger("pyffi.nif.data")
            # set up index and type dictionary
            self.blocks = [] # list of all blocks to be written
            self._block_index_dct = {} # maps block to block index
            block_type_list = [] # list of all block type strings
            block_type_dct = {} # maps block to block type string index
            self._string_list = []
            for root in self.roots:
                self._makeBlockList(root,
                                    self._block_index_dct,
                                    block_type_list, block_type_dct)
                for block in root.tree():
                    self._string_list.extend(
                        block.get_strings(self))
            self._string_list = list(set(self._string_list)) # ensure unique elements
            #print(self._string_list) # debug

            self.header.user_version = self.user_version # TODO dedicated type for user_version similar to FileVersion
            # for oblivion CS; apparently this is the version of the bhk blocks
            self.header.user_version_2 = self.user_version2
            self.header.num_blocks = len(self.blocks)
            self.header.num_block_types = len(block_type_list)
            self.header.block_types.update_size()
            for i, block_type in enumerate(block_type_list):
                self.header.block_types[i] = block_type
            self.header.block_type_index.update_size()
            for i, block in enumerate(self.blocks):
                self.header.block_type_index[i] = block_type_dct[block]
            self.header.num_strings = len(self._string_list)
            if self._string_list:
                self.header.max_string_length = max([len(s) for s in self._string_list])
            else:
                self.header.max_string_length = 0
            self.header.strings.update_size()
            for i, s in enumerate(self._string_list):
                self.header.strings[i] = s
            self.header.block_size.update_size()
            for i, block in enumerate(self.blocks):
                self.header.block_size[i] = block.get_size(data=self)
            #if verbose >= 2:
            #    print(hdr)

            # set up footer
            ftr = NifFormat.Footer()
            ftr.num_roots = len(self.roots)
            ftr.roots.update_size()
            for i, root in enumerate(self.roots):
                ftr.roots[i] = root

            # write the file
            logger.debug("Writing header")
            #logger.debug("%s" % self.header)
            self.header.write(stream, self)
            for block in self.blocks:
                # signal top level object if block is a root object
                if self.version < 0x0303000D and block in self.roots:
                    s = NifFormat.SizedString()
                    s.set_value("Top Level Object")
                    s.write(stream, self)
                if self.version >= 0x05000001:
                    if self.version <= 0x0A01006A:
                        # write zero dummy separator
                        stream.write('\x00\x00\x00\x00'.encode("ascii"))
                else:
                    # write block type string
                    s = NifFormat.SizedString()
                    assert(block_type_list[block_type_dct[block]]
                           == block.__class__.__name__) # debug
                    s.set_value(block.__class__.__name__)
                    s.write(stream, self)
                # write block index
                logger.debug("Writing %s block" % block.__class__.__name__)
                if self.version < 0x0303000D:
                    stream.write(struct.pack(self._byte_order + 'i',
                                             self._block_index_dct[block]))
                # write block
                block.write(stream, self)
            if self.version < 0x0303000D:
                s = NifFormat.SizedString()
                s.set_value("End Of File")
                s.write(stream)
            ftr.write(stream, self)

        def _makeBlockList(
            self, root, block_index_dct, block_type_list, block_type_dct):
            """This is a helper function for write to set up the list of all blocks,
            the block index map, and the block type map.

            :param root: The root block, whose tree is to be added to
                the block list.
            :type root: L{NifFormat.NiObject}
            :param block_index_dct: Dictionary mapping blocks in self.blocks to
                their block index.
            :type block_index_dct: dict
            :param block_type_list: List of all block types.
            :type block_type_list: list of str
            :param block_type_dct: Dictionary mapping blocks in self.blocks to
                their block type index.
            :type block_type_dct: dict
            """

            def _blockChildBeforeParent(block):
                """Determine whether block comes before its parent or not, depending
                on the block type.

                @todo: Move to the L{NifFormat.Data} class.

                :param block: The block to test.
                :type block: L{NifFormat.NiObject}
                :return: ``True`` if child should come first, ``False`` otherwise.
                """
                return (isinstance(block, NifFormat.bhkRefObject)
                        and not isinstance(block, NifFormat.bhkConstraint))

            # block already listed? if so, return
            if root in self.blocks:
                return
            # add block type to block type dictionary
            block_type = root.__class__.__name__
            # special case: NiDataStream stores part of data in block type list
            if block_type == "NiDataStream":
                block_type = ("NiDataStream\x01%i\x01%i"
                              % (root.usage, root.access.to_int(self)))
            try:
                block_type_dct[root] = block_type_list.index(block_type)
            except ValueError:
                block_type_dct[root] = len(block_type_list)
                block_type_list.append(block_type)

            # special case: add bhkConstraint entities before bhkConstraint
            # (these are actually links, not refs)
            if isinstance(root, NifFormat.bhkConstraint):
                for entity in root.entities:
                    self._makeBlockList(
                        entity, block_index_dct, block_type_list, block_type_dct)

            children_left = []
            # add children that come before the block
            # store any remaining children in children_left (processed later)
            for child in root.get_refs(data=self):
                if _blockChildBeforeParent(child):
                    self._makeBlockList(
                        child, block_index_dct, block_type_list, block_type_dct)
                else:
                    children_left.append(child)

            # add the block
            if self.version >= 0x0303000D:
                block_index_dct[root] = len(self.blocks)
            else:
                block_index_dct[root] = id(root)
            self.blocks.append(root)

            # add children that come after the block
            for child in children_left:
                self._makeBlockList(
                    child, block_index_dct, block_type_list, block_type_dct)

    # extensions of generated structures

    class Footer:
        def read(self, stream, data):
            StructBase.read(self, stream, data)
            modification = getattr(data, 'modification', None)
            if modification == "neosteam":
                extrabyte, = struct.unpack("<B", stream.read(1))
                if extrabyte != 0:
                    raise ValueError(
                        "Expected trailing zero byte in footer, "
                        "but got %i instead." % extrabyte)
            
        def write(self, stream, data):
            StructBase.write(self, stream, data)
            modification = getattr(data, 'modification', None)
            if modification == "neosteam":
                stream.write("\x00".encode("ascii"))
            

    class Header:
        def has_block_type(self, block_type):
            """Check if header has a particular block type.

            :raise ``ValueError``: If number of block types is zero
                (only nif versions 10.0.1.0 and up store block types
                in header).

            :param block_type: The block type.
            :type block_type: L{NifFormat.NiObject}
            :return: ``True`` if the header's list of block types has the given
                block type, or a subclass of it. ``False`` otherwise.
            :rtype: ``bool``
            """
            # check if we can check the block types at all
            if self.num_block_types == 0:
                raise ValueError("header does not store any block types")
            # quick first check, without hierarchy, using simple string comparisons
            if block_type.__name__.encode() in self.block_types:
                return True
            # slower check, using isinstance
            for data_block_type in self.block_types:
                data_block_type = data_block_type.decode("ascii")
                # NiDataStreams are special
                if data_block_type.startswith("NiDataStream\x01"):
                    data_block_type = "NiDataStream"
                if issubclass(getattr(NifFormat, data_block_type), block_type):
                    return True
            # requested block type is not in nif
            return False

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
            return (
                "[ %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f ]\n"
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
            if  (abs(self.m_11 - 1.0) > NifFormat.EPSILON
                 or abs(self.m_12) > NifFormat.EPSILON
                 or abs(self.m_13) > NifFormat.EPSILON
                 or abs(self.m_21) > NifFormat.EPSILON
                 or abs(self.m_22 - 1.0) > NifFormat.EPSILON
                 or abs(self.m_23) > NifFormat.EPSILON
                 or abs(self.m_31) > NifFormat.EPSILON
                 or abs(self.m_32) > NifFormat.EPSILON
                 or abs(self.m_33 - 1.0) > NifFormat.EPSILON):
                return False
            else:
                return True

        def get_copy(self):
            """Return a copy of the matrix."""
            mat = NifFormat.Matrix33()
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
            mat = NifFormat.Matrix33()
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
            # NOTE: 0.01 instead of NifFormat.EPSILON to work around bad nif files

            # calculate self * self^T
            # this should correspond to
            # (scale * rotation) * (scale * rotation)^T
            # = scale^2 * rotation * rotation^T
            # = scale^2 * 3x3 identity matrix
            self_transpose = self.get_transpose()
            mat = self * self_transpose

            # off diagonal elements should be zero
            if (abs(mat.m_12) + abs(mat.m_13)
                + abs(mat.m_21) + abs(mat.m_23)
                + abs(mat.m_31) + abs(mat.m_32)) > 0.01:
                return False

            # diagonal elements should be equal (to scale^2)
            if abs(mat.m_11 - mat.m_22) + abs(mat.m_22 - mat.m_33) > 0.01:
                return False

            return True

        def is_rotation(self):
            """Returns ``True`` if the matrix is a rotation matrix
            (a member of SO(3))."""
            # NOTE: 0.01 instead of NifFormat.EPSILON to work around bad nif files

            if not self.is_scale_rotation():
                return False
            if abs(self.get_determinant() - 1.0) > 0.01:
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
            scale = self.get_determinant()
            if scale < 0:
                return -((-scale)**(1.0/3.0))
            else:
                return scale**(1.0/3.0)

        def get_scale_rotation(self):
            """Decompose the matrix into scale and rotation, where scale is a float
            and rotation is a C{Matrix33}. Returns a pair (scale, rotation)."""
            rot = self.get_copy()
            scale = self.get_scale()
            if abs(scale) < NifFormat.EPSILON:
                raise ZeroDivisionError('scale is zero, unable to obtain rotation')
            rot /= scale
            return (scale, rot)

        def set_scale_rotation(self, scale, rotation):
            """Compose the matrix as the product of scale * rotation."""
            if not isinstance(scale, (float, int, long)):
                raise TypeError('scale must be float')
            if not isinstance(rotation, NifFormat.Matrix33):
                raise TypeError('rotation must be Matrix33')

            if not rotation.is_rotation():
                raise ValueError('rotation must be rotation matrix')

            self.m_11 = rotation.m_11 * scale
            self.m_12 = rotation.m_12 * scale
            self.m_13 = rotation.m_13 * scale
            self.m_21 = rotation.m_21 * scale
            self.m_22 = rotation.m_22 * scale
            self.m_23 = rotation.m_23 * scale
            self.m_31 = rotation.m_31 * scale
            self.m_32 = rotation.m_32 * scale
            self.m_33 = rotation.m_33 * scale

        def get_scale_quat(self):
            """Decompose matrix into scale and quaternion."""
            scale, rot = self.get_scale_rotation()
            quat = NifFormat.Quaternion()
            trace = 1.0 + rot.m_11 + rot.m_22 + rot.m_33

            if trace > NifFormat.EPSILON:
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
            return self.get_transpose() / (self.m_11**2 + self.m_12**2 + self.m_13**2)

        def __mul__(self, rhs):
            if isinstance(rhs, (float, int, long)):
                mat = NifFormat.Matrix33()
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
            elif isinstance(rhs, NifFormat.Vector3):
                raise TypeError(
                    "matrix*vector not supported; "
                    "please use left multiplication (vector*matrix)")
            elif isinstance(rhs, NifFormat.Matrix33):
                mat = NifFormat.Matrix33()
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
                mat = NifFormat.Matrix33()
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

        # py3k
        __truediv__ = __div__

        def __rmul__(self, lhs):
            if isinstance(lhs, (float, int, long)):
                return self * lhs # commutes
            else:
                raise TypeError(
                    "do not know how to multiply %s with Matrix33"%lhs.__class__)

        def __eq__(self, mat):
            if not isinstance(mat, NifFormat.Matrix33):
                raise TypeError(
                    "do not know how to compare Matrix33 and %s"%mat.__class__)
            if (abs(self.m_11 - mat.m_11) > NifFormat.EPSILON
                or abs(self.m_12 - mat.m_12) > NifFormat.EPSILON
                or abs(self.m_13 - mat.m_13) > NifFormat.EPSILON
                or abs(self.m_21 - mat.m_21) > NifFormat.EPSILON
                or abs(self.m_22 - mat.m_22) > NifFormat.EPSILON
                or abs(self.m_23 - mat.m_23) > NifFormat.EPSILON
                or abs(self.m_31 - mat.m_31) > NifFormat.EPSILON
                or abs(self.m_32 - mat.m_32) > NifFormat.EPSILON
                or abs(self.m_33 - mat.m_33) > NifFormat.EPSILON):
                return False
            return True

        def __ne__(self, mat):
            return not self.__eq__(mat)

        def __sub__(self, x):
            if isinstance(x, (NifFormat.Matrix33)):
                m = NifFormat.Matrix33()
                m.m_11 = self.m_11 - x.m_11
                m.m_12 = self.m_12 - x.m_12
                m.m_13 = self.m_13 - x.m_13
                m.m_21 = self.m_21 - x.m_21
                m.m_22 = self.m_22 - x.m_22
                m.m_23 = self.m_23 - x.m_23
                m.m_31 = self.m_31 - x.m_31
                m.m_32 = self.m_32 - x.m_32
                m.m_33 = self.m_33 - x.m_33
                return m
            elif isinstance(x, (int, long, float)):
                m = NifFormat.Matrix33()
                m.m_11 = self.m_11 - x
                m.m_12 = self.m_12 - x
                m.m_13 = self.m_13 - x
                m.m_21 = self.m_21 - x
                m.m_22 = self.m_22 - x
                m.m_23 = self.m_23 - x
                m.m_31 = self.m_31 - x
                m.m_32 = self.m_32 - x
                m.m_33 = self.m_33 - x
                return m
            else:
                raise TypeError("do not know how to substract Matrix33 and %s"
                                % x.__class__)

        def sup_norm(self):
            """Calculate supremum norm of matrix (maximum absolute value of all
            entries)."""
            return max(max(abs(elem) for elem in row)
                       for row in self.as_list())

    class Vector3:
        def as_list(self):
            return [self.x, self.y, self.z]

        def as_tuple(self):
            return (self.x, self.y, self.z)

        def norm(self, sqrt=math.sqrt):
            return sqrt(self.x*self.x + self.y*self.y + self.z*self.z)

        def normalize(self, ignore_error=False, sqrt=math.sqrt):
            # inlining norm() to reduce overhead
            try:
                factor = 1.0 / sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
            except ZeroDivisionError:
                if not ignore_error:
                    raise
                else:
                    return
            # inlining multiplication for speed
            self.x *= factor
            self.y *= factor
            self.z *= factor

        def normalized(self, ignore_error=False):
            vec = self.get_copy()
            vec.normalize(ignore_error=ignore_error)
            return vec

        def get_copy(self):
            v = NifFormat.Vector3()
            v.x = self.x
            v.y = self.y
            v.z = self.z
            return v

        def __str__(self):
            return "[ %6.3f %6.3f %6.3f ]"%(self.x, self.y, self.z)

        def __mul__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = self.x * x
                v.y = self.y * x
                v.z = self.z * x
                return v
            elif isinstance(x, NifFormat.Vector3):
                return self.x * x.x + self.y * x.y + self.z * x.z
            elif isinstance(x, NifFormat.Matrix33):
                v = NifFormat.Vector3()
                v.x = self.x * x.m_11 + self.y * x.m_21 + self.z * x.m_31
                v.y = self.x * x.m_12 + self.y * x.m_22 + self.z * x.m_32
                v.z = self.x * x.m_13 + self.y * x.m_23 + self.z * x.m_33
                return v
            elif isinstance(x, NifFormat.Matrix44):
                return self * x.get_matrix_33() + x.get_translation()
            else:
                raise TypeError("do not know how to multiply Vector3 with %s"%x.__class__)

        def __rmul__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = x * self.x
                v.y = x * self.y
                v.z = x * self.z
                return v
            else:
                raise TypeError("do not know how to multiply %s and Vector3"%x.__class__)

        def __div__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = self.x / x
                v.y = self.y / x
                v.z = self.z / x
                return v
            else:
                raise TypeError("do not know how to divide Vector3 and %s"%x.__class__)

        # py3k
        __truediv__ = __div__

        def __add__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = self.x + x
                v.y = self.y + x
                v.z = self.z + x
                return v
            elif isinstance(x, NifFormat.Vector3):
                v = NifFormat.Vector3()
                v.x = self.x + x.x
                v.y = self.y + x.y
                v.z = self.z + x.z
                return v
            else:
                raise TypeError("do not know how to add Vector3 and %s"%x.__class__)

        def __radd__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = x + self.x
                v.y = x + self.y
                v.z = x + self.z
                return v
            else:
                raise TypeError("do not know how to add %s and Vector3"%x.__class__)

        def __sub__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = self.x - x
                v.y = self.y - x
                v.z = self.z - x
                return v
            elif isinstance(x, NifFormat.Vector3):
                v = NifFormat.Vector3()
                v.x = self.x - x.x
                v.y = self.y - x.y
                v.z = self.z - x.z
                return v
            else:
                raise TypeError("do not know how to substract Vector3 and %s"%x.__class__)

        def __rsub__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.Vector3()
                v.x = x - self.x
                v.y = x - self.y
                v.z = x - self.z
                return v
            else:
                raise TypeError("do not know how to substract %s and Vector3"%x.__class__)

        def __neg__(self):
            v = NifFormat.Vector3()
            v.x = -self.x
            v.y = -self.y
            v.z = -self.z
            return v

        # cross product
        def crossproduct(self, x):
            if isinstance(x, NifFormat.Vector3):
                v = NifFormat.Vector3()
                v.x = self.y*x.z - self.z*x.y
                v.y = self.z*x.x - self.x*x.z
                v.z = self.x*x.y - self.y*x.x
                return v
            else:
                raise TypeError("do not know how to calculate crossproduct of Vector3 and %s"%x.__class__)

        def __eq__(self, x):
            if isinstance(x, type(None)):
                return False
            if not isinstance(x, NifFormat.Vector3):
                raise TypeError("do not know how to compare Vector3 and %s"%x.__class__)
            if abs(self.x - x.x) > NifFormat.EPSILON: return False
            if abs(self.y - x.y) > NifFormat.EPSILON: return False
            if abs(self.z - x.z) > NifFormat.EPSILON: return False
            return True

        def __ne__(self, x):
            return not self.__eq__(x)

    class Vector4:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> vec = NifFormat.Vector4()
        >>> vec.x = 1.0
        >>> vec.y = 2.0
        >>> vec.z = 3.0
        >>> vec.w = 4.0
        >>> print(vec)
        [  1.000  2.000  3.000  4.000 ]
        >>> vec.as_list()
        [1.0, 2.0, 3.0, 4.0]
        >>> vec.as_tuple()
        (1.0, 2.0, 3.0, 4.0)
        >>> print(vec.get_vector_3())
        [  1.000  2.000  3.000 ]
        >>> vec2 = NifFormat.Vector4()
        >>> vec == vec2
        False
        >>> vec2.x = 1.0
        >>> vec2.y = 2.0
        >>> vec2.z = 3.0
        >>> vec2.w = 4.0
        >>> vec == vec2
        True
        """

        def as_list(self):
            return [self.x, self.y, self.z, self.w]

        def as_tuple(self):
            return (self.x, self.y, self.z, self.w)

        def get_copy(self):
            v = NifFormat.Vector4()
            v.x = self.x
            v.y = self.y
            v.z = self.z
            v.w = self.w
            return v

        def get_vector_3(self):
            v = NifFormat.Vector3()
            v.x = self.x
            v.y = self.y
            v.z = self.z
            return v

        def __str__(self):
            return "[ %6.3f %6.3f %6.3f %6.3f ]"%(self.x, self.y, self.z, self.w)

        def __eq__(self, rhs):
            if isinstance(rhs, type(None)):
                return False
            if not isinstance(rhs, NifFormat.Vector4):
                raise TypeError(
                    "do not know how to compare Vector4 and %s" % rhs.__class__)
            if abs(self.x - rhs.x) > NifFormat.EPSILON: return False
            if abs(self.y - rhs.y) > NifFormat.EPSILON: return False
            if abs(self.z - rhs.z) > NifFormat.EPSILON: return False
            if abs(self.w - rhs.w) > NifFormat.EPSILON: return False
            return True

        def __ne__(self, rhs):
            return not self.__eq__(rhs)

    class SkinPartition:
        def get_triangles(self):
            """Get list of triangles of this partition.
            """
            # strips?
            if self.num_strips:
                for tri in pyffi.utils.tristrip.triangulate(self.strips):
                    yield tri
            # no strips, do triangles
            else:
                for tri in self.triangles:
                    yield (tri.v_1, tri.v_2, tri.v_3)

        def get_mapped_triangles(self):
            """Get list of triangles of this partition (mapping into the
            geometry data vertex list).
            """
            for tri in self.get_triangles():
                yield tuple(self.vertex_map[v_index] for v_index in tri)

    class bhkBoxShape:
        def apply_scale(self, scale):
            """Apply scale factor C{scale} on data."""
            # apply scale on dimensions
            self.dimensions.x *= scale
            self.dimensions.y *= scale
            self.dimensions.z *= scale
            self.minimum_size  *= scale

        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            # the dimensions describe half the size of the box in each dimension
            # so the length of a single edge is dimension.dir * 2
            mass, inertia = pyffi.utils.inertia.getMassInertiaBox(
                (self.dimensions.x * 2, self.dimensions.y * 2, self.dimensions.z * 2),
                density = density, solid = solid)
            return mass, (0,0,0), inertia

    class bhkCapsuleShape:
        def apply_scale(self, scale):
            """Apply scale factor <scale> on data."""
            # apply scale on dimensions
            self.radius *= scale
            self.radius_1 *= scale
            self.radius_2 *= scale
            self.first_point.x *= scale
            self.first_point.y *= scale
            self.first_point.z *= scale
            self.second_point.x *= scale
            self.second_point.y *= scale
            self.second_point.z *= scale

        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            # (assumes self.radius == self.radius_1 == self.radius_2)
            length = (self.first_point - self.second_point).norm()
            mass, inertia = pyffi.utils.inertia.getMassInertiaCapsule(
                radius = self.radius, length = length,
                density = density, solid = solid)
            # now fix inertia so it is expressed in the right coordinates
            # need a transform that maps (0,0,length/2) on (second - first) / 2
            # and (0,0,-length/2) on (first - second)/2
            vec1 = ((self.second_point - self.first_point) / length).as_tuple()
            # find an orthogonal vector to vec1
            index = min(enumerate(vec1), key=lambda val: abs(val[1]))[0]
            vec2 = vecCrossProduct(vec1, tuple((1 if i == index else 0)
                                               for i in xrange(3)))
            vec2 = vecscalarMul(vec2, 1/vecNorm(vec2))
            # find an orthogonal vector to vec1 and vec2
            vec3 = vecCrossProduct(vec1, vec2)
            # get transform matrix
            transform_transposed = (vec2, vec3, vec1) # this is effectively the transposed of our transform
            transform = matTransposed(transform_transposed)
            # check the result (debug)
            assert(vecDistance(matvecMul(transform, (0,0,1)), vec1) < 0.0001)
            assert(abs(matDeterminant(transform) - 1) < 0.0001)
            # transform the inertia tensor
            inertia = matMul(matMul(transform_transposed, inertia), transform)
            return (mass,
                    ((self.first_point + self.second_point) * 0.5).as_tuple(),
                    inertia)

    class bhkConstraint:
        def get_transform_a_b(self, parent):
            """Returns the transform of the first entity relative to the second
            entity. Root is simply a nif block that is a common parent to both
            blocks."""
            # check entities
            if self.num_entities != 2:
                raise ValueError(
                    "cannot get tranform for constraint "
                    "that hasn't exactly 2 entities")
            # find transform of entity A relative to entity B

            # find chains from parent to A and B entities
            chainA = parent.find_chain(self.entities[0])
            chainB = parent.find_chain(self.entities[1])
            # validate the chains
            assert(isinstance(chainA[-1], NifFormat.bhkRigidBody))
            assert(isinstance(chainA[-2], NifFormat.NiCollisionObject))
            assert(isinstance(chainA[-3], NifFormat.NiNode))
            assert(isinstance(chainB[-1], NifFormat.bhkRigidBody))
            assert(isinstance(chainB[-2], NifFormat.NiCollisionObject))
            assert(isinstance(chainB[-3], NifFormat.NiNode))
            # return the relative transform
            return (chainA[-3].get_transform(relative_to = parent)
                    * chainB[-3].get_transform(relative_to = parent).get_inverse())

    class bhkConvexVerticesShape:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < NifFormat.EPSILON: return
            for v in self.vertices:
                v.x *= scale
                v.y *= scale
                v.z *= scale
            for n in self.normals:
                n.w *= scale

        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            # first find an enumeration of all triangles making up the convex shape
            vertices, triangles = pyffi.utils.quickhull.qhull3d(
                [vert.as_tuple() for vert in self.vertices])
            # now calculate mass, center, and inertia
            return pyffi.utils.inertia.get_mass_center_inertia_polyhedron(
                vertices, triangles, density = density, solid = solid)

    class bhkLimitedHingeConstraint:
        def apply_scale(self, scale):
            """Scale data."""
            # apply scale on transform
            self.limited_hinge.pivot_a.x *= scale
            self.limited_hinge.pivot_a.y *= scale
            self.limited_hinge.pivot_a.z *= scale
            self.limited_hinge.pivot_b.x *= scale
            self.limited_hinge.pivot_b.y *= scale
            self.limited_hinge.pivot_b.z *= scale

        def update_a_b(self, parent):
            """Update the B data from the A data. The parent argument is simply a
            common parent to the entities."""
            self.limited_hinge.update_a_b(self.get_transform_a_b(parent))

    class bhkListShape:
        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return center of gravity and area."""
            subshapes_mci = [ subshape.get_mass_center_inertia(density = density,
                                                            solid = solid)
                              for subshape in self.sub_shapes ]
            total_mass = 0
            total_center = (0, 0, 0)
            total_inertia = ((0, 0, 0), (0, 0, 0), (0, 0, 0))

            # get total mass
            for mass, center, inertia in subshapes_mci:
                total_mass += mass
            if total_mass == 0:
                return 0, (0, 0, 0), ((0, 0, 0), (0, 0, 0), (0, 0, 0))

            # get average center and inertia
            for mass, center, inertia in subshapes_mci:
                total_center = vecAdd(total_center,
                                      vecscalarMul(center, mass / total_mass))
                total_inertia = matAdd(total_inertia, inertia)
            return total_mass, total_center, total_inertia

        def add_shape(self, shape, front = False):
            """Add shape to list."""
            # check if it's already there
            if shape in self.sub_shapes: return
            # increase number of shapes
            num_shapes = self.num_sub_shapes
            self.num_sub_shapes = num_shapes + 1
            self.sub_shapes.update_size()
            # add the shape
            if not front:
                self.sub_shapes[num_shapes] = shape
            else:
                for i in xrange(num_shapes, 0, -1):
                    self.sub_shapes[i] = self.sub_shapes[i-1]
                self.sub_shapes[0] = shape
            # expand list of unknown ints as well
            self.num_unknown_ints = num_shapes + 1
            self.unknown_ints.update_size()

        def remove_shape(self, shape):
            """Remove a shape from the shape list."""
            # get list of shapes excluding the shape to remove
            shapes = [s for s in self.sub_shapes if s != shape]
            # set sub_shapes to this list
            self.num_sub_shapes = len(shapes)
            self.sub_shapes.update_size()
            for i, s in enumerate(shapes):
                self.sub_shapes[i] = s
            # update unknown ints
            self.num_unknown_ints = len(shapes)
            self.unknown_ints.update_size()

    class bhkMalleableConstraint:
        def apply_scale(self, scale):
            """Scale data."""
            # apply scale on transform
            self.ragdoll.pivot_a.x *= scale
            self.ragdoll.pivot_a.y *= scale
            self.ragdoll.pivot_a.z *= scale
            self.ragdoll.pivot_b.x *= scale
            self.ragdoll.pivot_b.y *= scale
            self.ragdoll.pivot_b.z *= scale
            self.limited_hinge.pivot_a.x *= scale
            self.limited_hinge.pivot_a.y *= scale
            self.limited_hinge.pivot_a.z *= scale
            self.limited_hinge.pivot_b.x *= scale
            self.limited_hinge.pivot_b.y *= scale
            self.limited_hinge.pivot_b.z *= scale

        def update_a_b(self, parent):
            """Update the B data from the A data."""
            transform = self.get_transform_a_b(parent)
            self.limited_hinge.update_a_b(transform)
            self.ragdoll.update_a_b(transform)

    class bhkMoppBvTreeShape:
        def get_mass_center_inertia(self, density=1, solid=True):
            """Return mass, center of gravity, and inertia tensor."""
            return self.get_shape_mass_center_inertia(
                density=density, solid=solid)

        def update_origin_scale(self):
            """Update scale and origin."""
            minx = min(v.x for v in self.shape.data.vertices)
            miny = min(v.y for v in self.shape.data.vertices)
            minz = min(v.z for v in self.shape.data.vertices)
            maxx = max(v.x for v in self.shape.data.vertices)
            maxy = max(v.y for v in self.shape.data.vertices)
            maxz = max(v.z for v in self.shape.data.vertices)
            self.origin.x = minx - 0.1
            self.origin.y = miny - 0.1
            self.origin.z = minz - 0.1
            self.scale = (256*256*254) / (0.2+max([maxx-minx,maxy-miny,maxz-minz]))

        def update_mopp(self):
            """Update the MOPP data, scale, and origin, and welding info.

            @deprecated: use update_mopp_welding instead
            """
            self.update_mopp_welding()

        def update_mopp_welding(self):
            """Update the MOPP data, scale, and origin, and welding info."""
            logger = logging.getLogger("pyffi.mopp")
            # check type of shape
            if not isinstance(self.shape, NifFormat.bhkPackedNiTriStripsShape):
                raise ValueError(
                    "expected bhkPackedNiTriStripsShape on mopp"
                    " but got %s instead" % self.shape.__class__.__name__)
            # first try with pyffi.utils.mopp
            failed = False
            try:
                print(pyffi.utils.mopp.getMopperCredits())
            except (OSError, RuntimeError):
                failed = True
            else:
                # find material indices per triangle
                material_per_vertex = []
                for subshape in self.shape.get_sub_shapes():
                    material_per_vertex += (
                        [subshape.material] * subshape.num_vertices)
                material_per_triangle = [
                    material_per_vertex[hktri.triangle.v_1]
                    for hktri in self.shape.data.triangles]
                # compute havok info
                try:
                    origin, scale, mopp, welding_infos \
                    = pyffi.utils.mopp.getMopperOriginScaleCodeWelding(
                        [vert.as_tuple() for vert in self.shape.data.vertices],
                        [(hktri.triangle.v_1,
                          hktri.triangle.v_2,
                          hktri.triangle.v_3)
                         for hktri in self.shape.data.triangles],
                        material_per_triangle)
                except (OSError, RuntimeError):
                    failed = True
                else:
                    # must use calculated scale and origin
                    self.scale = scale
                    self.origin.x = origin[0]
                    self.origin.y = origin[1]
                    self.origin.z = origin[2]
            # if havok's mopper failed, do a simple mopp
            if failed:
                logger.exception(
                    "Havok mopp generator failed, falling back on simple mopp "
                    "(but collisions may be flawed in-game!)."
                    "If you are using the PyFFI that was shipped with Blender, "
                    "and you are on Windows, then you may wish to install the "
                    "full version of PyFFI from "
                    "http://pyffi.sourceforge.net/ "
                    "instead, which includes the (closed source) "
                    "Havok mopp generator.")
                self.update_origin_scale()
                mopp = self._makeSimpleMopp()
                # no welding info
                welding_infos = []

            # delete mopp and replace with new data
            self.mopp_data_size = len(mopp)
            self.mopp_data.update_size()
            for i, b in enumerate(mopp):
                self.mopp_data[i] = b

            # update welding information
            for hktri, welding_info in izip(self.shape.data.triangles, welding_infos):
                hktri.welding_info = welding_info

        def _makeSimpleMopp(self):
            """Make a simple mopp."""
            mopp = [] # the mopp 'assembly' script
            self._q = 256*256 / self.scale # quantization factor

            # opcodes
            BOUNDX = 0x26
            BOUNDY = 0x27
            BOUNDZ = 0x28
            TESTX = 0x10
            TESTY = 0x11
            TESTZ = 0x12

            # add first crude bounding box checks
            self._vertsceil  = [ self._moppCeil(v) for v in self.shape.data.vertices ]
            self._vertsfloor = [ self._moppFloor(v) for v in self.shape.data.vertices ]
            minx = min([ v[0] for v in self._vertsfloor ])
            miny = min([ v[1] for v in self._vertsfloor ])
            minz = min([ v[2] for v in self._vertsfloor ])
            maxx = max([ v[0] for v in self._vertsceil ])
            maxy = max([ v[1] for v in self._vertsceil ])
            maxz = max([ v[2] for v in self._vertsceil ])
            if minx < 0 or miny < 0 or minz < 0: raise ValueError("cannot update mopp tree with invalid origin")
            if maxx > 255 or maxy > 255 or maxz > 255: raise ValueError("cannot update mopp tree with invalid scale")
            mopp.extend([BOUNDZ, minz, maxz])
            mopp.extend([BOUNDY, miny, maxy])
            mopp.extend([BOUNDX, minx, maxx])

            # add tree using subsequent X-Y-Z splits
            # (slow and no noticable difference from other simple tree so deactivated)
            #tris = range(len(self.shape.data.triangles))
            #tree = self.split_triangles(tris, [[minx,maxx],[miny,maxy],[minz,maxz]])
            #mopp += self.mopp_from_tree(tree)

            # add a trivial tree
            # this prevents the player of walking through the model
            # but arrows may still fly through
            numtriangles = len(self.shape.data.triangles)
            i = 0x30
            for t in xrange(numtriangles-1):
                 mopp.extend([TESTZ, maxz, 0, 1, i])
                 i += 1
                 if i == 0x50:
                     mopp.extend([0x09, 0x20]) # increment triangle offset
                     i = 0x30
            mopp.extend([i])

            return mopp

        def _moppCeil(self, v):
            moppx = int((v.x + 0.1 - self.origin.x) / self._q + 0.99999999)
            moppy = int((v.y + 0.1 - self.origin.y) / self._q + 0.99999999)
            moppz = int((v.z + 0.1 - self.origin.z) / self._q + 0.99999999)
            return [moppx, moppy, moppz]

        def _moppFloor(self, v):
            moppx = int((v.x - 0.1 - self.origin.x) / self._q)
            moppy = int((v.y - 0.1 - self.origin.y) / self._q)
            moppz = int((v.z - 0.1 - self.origin.z) / self._q)
            return [moppx, moppy, moppz]

        def split_triangles(self, ts, bbox, dir=0):
            """Direction 0=X, 1=Y, 2=Z"""
            btest = [] # for bounding box tests
            test = [] # for branch command
            # check bounding box
            tris = [ t.triangle for t in self.shape.data.triangles ]
            tsverts = [ tris[t].v_1 for t in ts] + [ tris[t].v_2 for t in ts] + [ tris[t].v_3 for t in ts]
            minx = min([self._vertsfloor[v][0] for v in tsverts])
            miny = min([self._vertsfloor[v][1] for v in tsverts])
            minz = min([self._vertsfloor[v][2] for v in tsverts])
            maxx = max([self._vertsceil[v][0] for v in tsverts])
            maxy = max([self._vertsceil[v][1] for v in tsverts])
            maxz = max([self._vertsceil[v][2] for v in tsverts])
            # add bounding box checks if it's reduced in a direction
            if (maxx - minx < bbox[0][1] - bbox[0][0]):
                btest += [ 0x26, minx, maxx ]
                bbox[0][0] = minx
                bbox[0][1] = maxx
            if (maxy - miny < bbox[1][1] - bbox[1][0]):
                btest += [ 0x27, miny, maxy ]
                bbox[1][0] = miny
                bbox[1][1] = maxy
            if (maxz - minz < bbox[2][1] - bbox[2][0]):
                btest += [ 0x28, minz, maxz ]
                bbox[2][0] = minz
                bbox[2][1] = maxz
            # if only one triangle, no further split needed
            if len(ts) == 1:
                if ts[0] < 32:
                    return [ btest, [ 0x30 + ts[0] ], [], [] ]
                elif ts[0] < 256:
                    return [ btest, [ 0x50, ts[0] ], [], [] ]
                else:
                    return [ btest, [ 0x51, ts[0] >> 8, ts[0] & 255 ], [], [] ]
            # sort triangles in required direction
            ts.sort(key = lambda t: max(self._vertsceil[tris[t].v_1][dir], self._vertsceil[tris[t].v_2][dir], self._vertsceil[tris[t].v_3][dir]))
            # split into two
            ts1 = ts[:len(ts)/2]
            ts2 = ts[len(ts)/2:]
            # get maximum coordinate of small group
            ts1verts = [ tris[t].v_1 for t in ts1] + [ tris[t].v_2 for t in ts1] + [ tris[t].v_3 for t in ts1]
            ts2verts = [ tris[t].v_1 for t in ts2] + [ tris[t].v_2 for t in ts2] + [ tris[t].v_3 for t in ts2]
            ts1max = max([self._vertsceil[v][dir] for v in ts1verts])
            # get minimum coordinate of large group
            ts2min = min([self._vertsfloor[v][dir] for v in ts2verts])
            # set up test
            test += [0x10+dir, ts1max, ts2min]
            # set up new bounding boxes for each subtree
            # make copy
            bbox1 = [[bbox[0][0],bbox[0][1]],[bbox[1][0],bbox[1][1]],[bbox[2][0],bbox[2][1]]]
            bbox2 = [[bbox[0][0],bbox[0][1]],[bbox[1][0],bbox[1][1]],[bbox[2][0],bbox[2][1]]]
            # update bound in test direction
            bbox1[dir][1] = ts1max
            bbox2[dir][0] = ts2min
            # return result
            nextdir = dir+1
            if nextdir == 3: nextdir = 0
            return [btest, test, self.split_triangles(ts1, bbox1, nextdir), self.split_triangles(ts2, bbox2, nextdir)]

        def mopp_from_tree(self, tree):
            if tree[1][0] in xrange(0x30, 0x52):
                return tree[0] + tree[1]
            mopp = tree[0] + tree[1]
            submopp1 = self.mopp_from_tree(tree[2])
            submopp2 = self.mopp_from_tree(tree[3])
            if len(submopp1) < 256:
                mopp += [ len(submopp1) ]
                mopp += submopp1
                mopp += submopp2
            else:
                jump = len(submopp2)
                if jump <= 255:
                    mopp += [2, 0x05, jump]
                else:
                    mopp += [3, 0x06, jump >> 8, jump & 255]
                mopp += submopp2
                mopp += submopp1
            return mopp

        # ported and extended from NifVis/bhkMoppBvTreeShape.py
        def parse_mopp(self, start = 0, depth = 0, toffset = 0, verbose = False):
            """The mopp data is printed to the debug channel
            while parsed. Returns list of indices into mopp data of the bytes
            processed and a list of triangle indices encountered.

            The verbose argument is ignored (and is deprecated).
            """
            class Message:
                def __init__(self):
                    self.logger = logging.getLogger("pyffi.mopp")
                    self.msg = ""

                def append(self, *args):
                    self.msg += " ".join(str(arg) for arg in args) + " "
                    return self

                def debug(self):
                    if self.msg:
                        self.logger.debug(self.msg)
                        self.msg = ""

                def error(self):
                    self.logger.error(self.msg)
                    self.msg = ""

            mopp = self.mopp_data # shortcut notation
            ids = [] # indices of bytes processed
            tris = [] # triangle indices
            i = start # current index
            ret = False # set to True if an opcode signals a triangle index
            while i < self.mopp_data_size and not ret:
                # get opcode and print it
                code = mopp[i]
                msg = Message()
                msg.append("%4i:"%i + "  "*depth + '0x%02X ' % code)

                if code == 0x09:
                    # increment triangle offset
                    toffset += mopp[i+1]
                    msg.append(mopp[i+1])
                    msg.append('%i [ triangle offset += %i, offset is now %i ]'
                                    % (mopp[i+1], mopp[i+1], toffset))
                    ids.extend([i,i+1])
                    i += 2

                elif code in [ 0x0A ]:
                    # increment triangle offset
                    toffset += mopp[i+1]*256 + mopp[i+2]
                    msg.append(mopp[i+1],mopp[i+2])
                    msg.append('[ triangle offset += %i, offset is now %i ]'
                                    % (mopp[i+1]*256 + mopp[i+2], toffset))
                    ids.extend([i,i+1,i+2])
                    i += 3

                elif code in [ 0x0B ]:
                    # unsure about first two arguments, but the 3rd and 4th set triangle offset
                    toffset = 256*mopp[i+3] + mopp[i+4]
                    msg.append(mopp[i+1],mopp[i+2],mopp[i+3],mopp[i+4])
                    msg.append('[ triangle offset = %i ]' % toffset)
                    ids.extend([i,i+1,i+2,i+3,i+4])
                    i += 5

                elif code in xrange(0x30,0x50):
                    # triangle compact
                    msg.append('[ triangle %i ]'%(code-0x30+toffset))
                    ids.append(i)
                    tris.append(code-0x30+toffset)
                    i += 1
                    ret = True

                elif code == 0x50:
                    # triangle byte
                    msg.append(mopp[i+1])
                    msg.append('[ triangle %i ]'%(mopp[i+1]+toffset))
                    ids.extend([i,i+1])
                    tris.append(mopp[i+1]+toffset)
                    i += 2
                    ret = True

                elif code in [ 0x51 ]:
                    # triangle short
                    t = mopp[i+1]*256 + mopp[i+2] + toffset
                    msg.append(mopp[i+1],mopp[i+2])
                    msg.append('[ triangle %i ]' % t)
                    ids.extend([i,i+1,i+2])
                    tris.append(t)
                    i += 3
                    ret = True

                elif code in [ 0x53 ]:
                    # triangle short?
                    t = mopp[i+3]*256 + mopp[i+4] + toffset
                    msg.append(mopp[i+1],mopp[i+2],mopp[i+3],mopp[i+4])
                    msg.append('[ triangle %i ]' % t)
                    ids.extend([i,i+1,i+2,i+3,i+4])
                    tris.append(t)
                    i += 5
                    ret = True

                elif code in [ 0x05 ]:
                    # byte jump
                    msg.append('[ jump -> %i: ]'%(i+2+mopp[i+1]))
                    ids.extend([i,i+1])
                    i += 2+mopp[i+1]

                elif code in [ 0x06 ]:
                    # short jump
                    jump = mopp[i+1]*256 + mopp[i+2]
                    msg.append('[ jump -> %i: ]'%(i+3+jump))
                    ids.extend([i,i+1,i+2])
                    i += 3+jump

                elif code in [0x10,0x11,0x12, 0x13,0x14,0x15, 0x16,0x17,0x18, 0x19, 0x1A, 0x1B, 0x1C]:
                    # compact if-then-else with two arguments
                    msg.append(mopp[i+1], mopp[i+2])
                    if code == 0x10:
                        msg.append('[ branch X')
                    elif code == 0x11:
                        msg.append('[ branch Y')
                    elif code == 0x12:
                        msg.append('[ branch Z')
                    else:
                        msg.append('[ branch ?')
                    msg.append('-> %i: %i: ]'%(i+4,i+4+mopp[i+3]))
                    msg.debug()
                    msg.append("     " + "  "*depth + 'if:')
                    msg.debug()
                    idssub1, trissub1 = self.parse_mopp(start = i+4, depth = depth+1, toffset = toffset, verbose = verbose)
                    msg.append("     " + "  "*depth + 'else:')
                    msg.debug()
                    idssub2, trissub2 = self.parse_mopp(start = i+4+mopp[i+3], depth = depth+1, toffset = toffset, verbose = verbose)
                    ids.extend([i,i+1,i+2,i+3])
                    ids.extend(idssub1)
                    ids.extend(idssub2)
                    tris.extend(trissub1)
                    tris.extend(trissub2)
                    ret = True

                elif code in [0x20,0x21,0x22]:
                    # compact if-then-else with one argument
                    msg.append(mopp[i+1], '[ branch ? -> %i: %i: ]'%(i+3,i+3+mopp[i+2])).debug()
                    msg.append("     " + "  "*depth + 'if:').debug()
                    idssub1, trissub1 = self.parse_mopp(start = i+3, depth = depth+1, toffset = toffset, verbose = verbose)
                    msg.append("     " + "  "*depth + 'else:').debug()
                    idssub2, trissub2 = self.parse_mopp(start = i+3+mopp[i+2], depth = depth+1, toffset = toffset, verbose = verbose)
                    ids.extend([i,i+1,i+2])
                    ids.extend(idssub1)
                    ids.extend(idssub2)
                    tris.extend(trissub1)
                    tris.extend(trissub2)
                    ret = True

                elif code in [0x23,0x24,0x25]: # short if x <= a then 1; if x > b then 2;
                    jump1 = mopp[i+3] * 256 + mopp[i+4]
                    jump2 = mopp[i+5] * 256 + mopp[i+6]
                    msg.append(mopp[i+1], mopp[i+2], '[ branch ? -> %i: %i: ]'%(i+7+jump1,i+7+jump2)).debug()
                    msg.append("     " + "  "*depth + 'if:').debug()
                    idssub1, trissub1 = self.parse_mopp(start = i+7+jump1, depth = depth+1, toffset = toffset, verbose = verbose)
                    msg.append("     " + "  "*depth + 'else:').debug()
                    idssub2, trissub2 = self.parse_mopp(start = i+7+jump2, depth = depth+1, toffset = toffset, verbose = verbose)
                    ids.extend([i,i+1,i+2,i+3,i+4,i+5,i+6])
                    ids.extend(idssub1)
                    ids.extend(idssub2)
                    tris.extend(trissub1)
                    tris.extend(trissub2)
                    ret = True
                elif code in [0x26,0x27,0x28]:
                    msg.append(mopp[i+1], mopp[i+2])
                    if code == 0x26:
                        msg.append('[ bound X ]')
                    elif code == 0x27:
                        msg.append('[ bound Y ]')
                    elif code == 0x28:
                        msg.append('[ bound Z ]')
                    ids.extend([i,i+1,i+2])
                    i += 3
                elif code in [0x01, 0x02, 0x03, 0x04]:
                    msg.append(mopp[i+1], mopp[i+2], mopp[i+3], '[ bound XYZ? ]')
                    ids.extend([i,i+1,i+2,i+3])
                    i += 4
                else:
                    msg.append("unknown mopp code 0x%02X"%code).error()
                    msg.append("following bytes are").debug()
                    extrabytes = [mopp[j] for j in xrange(i+1,min(self.mopp_data_size,i+10))]
                    extraindex = [j       for j in xrange(i+1,min(self.mopp_data_size,i+10))]
                    msg.append(extrabytes).debug()
                    for b, j in zip(extrabytes, extraindex):
                        if j+b+1 < self.mopp_data_size:
                            msg.append("opcode after jump %i is 0x%02X"%(b,mopp[j+b+1]), [mopp[k] for k in xrange(j+b+2,min(self.mopp_data_size,j+b+11))]).debug()
                    raise ValueError("unknown mopp opcode 0x%02X"%code)

                msg.debug()

            return ids, tris

    class bhkMultiSphereShape:
        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return center of gravity and area."""
            subshapes_mci = [
                (mass, center, inertia)
                for (mass, inertia), center in
                izip( ( pyffi.utils.inertia.getMassInertiaSphere(radius = sphere.radius,
                                                                 density = density, solid = solid)
                        for sphere in self.spheres ),
                      ( sphere.center.as_tuple() for sphere in self.spheres ) ) ]
            total_mass = 0
            total_center = (0, 0, 0)
            total_inertia = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
            for mass, center, inertia in subshapes_mci:
                total_mass += mass
                total_center = vecAdd(total_center,
                                      vecscalarMul(center, mass / total_mass))
                total_inertia = matAdd(total_inertia, inertia)
            return total_mass, total_center, total_inertia

    class bhkNiTriStripsShape:
        def get_interchangeable_packed_shape(self):
            """Returns a bhkPackedNiTriStripsShape block that is geometrically
            interchangeable.
            """
            # get all vertices, triangles, and calculate normals
            vertices = []
            normals = []
            triangles = []
            for strip in self.strips_data:
                triangles.extend(
                    (tri1 + len(vertices),
                     tri2 + len(vertices),
                     tri3 + len(vertices))
                    for tri1, tri2, tri3 in strip.get_triangles())
                vertices.extend(
                    # scaling factor 1/7 applied in add_shape later
                    vert.as_tuple() for vert in strip.vertices)
                normals.extend(
                    (strip.vertices[tri2] - strip.vertices[tri1]).crossproduct(
                        strip.vertices[tri3] - strip.vertices[tri1])
                    .normalized(ignore_error=True)
                    .as_tuple()
                    for tri1, tri2, tri3 in strip.get_triangles())
            # create packed shape and add geometry
            packed = NifFormat.bhkPackedNiTriStripsShape()
            packed.add_shape(
                triangles=triangles,
                normals=normals,
                vertices=vertices,
                # default layer 1 (static collision)
                layer=self.data_layers[0].layer if self.data_layers else 1,
                material=self.material)
            # set unknowns
            packed.unknown_floats[2] = 0.1
            packed.unknown_floats[4] = 1.0
            packed.unknown_floats[5] = 1.0
            packed.unknown_floats[6] = 1.0
            packed.unknown_floats[8] = 0.1
            packed.scale = 1.0
            packed.unknown_floats_2[0] = 1.0
            packed.unknown_floats_2[1] = 1.0
            # return result
            return packed

        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            # first find mass, center, and inertia of all shapes
            subshapes_mci = []
            for data in self.strips_data:
                subshapes_mci.append(
                    pyffi.utils.inertia.get_mass_center_inertia_polyhedron(
                        [ vert.as_tuple() for vert in data.vertices ],
                        [ triangle for triangle in data.get_triangles() ],
                        density = density, solid = solid))

            # now calculate mass, center, and inertia
            total_mass = 0
            total_center = (0, 0, 0)
            total_inertia = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
            for mass, center, inertia in subshapes_mci:
                total_mass += mass
                total_center = vecAdd(total_center,
                                      vecscalarMul(center, mass / total_mass))
                total_inertia = matAdd(total_inertia, inertia)
            return total_mass, total_center, total_inertia

    class bhkPackedNiTriStripsShape:
        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            return pyffi.utils.inertia.get_mass_center_inertia_polyhedron(
                [ vert.as_tuple() for vert in self.data.vertices ],
                [ ( hktriangle.triangle.v_1,
                    hktriangle.triangle.v_2,
                    hktriangle.triangle.v_3 )
                  for hktriangle in self.data.triangles ],
                density = density, solid = solid)

        def get_sub_shapes(self):
            """Return sub shapes (works for both Oblivion and Fallout 3)."""
            if self.data and self.data.sub_shapes:
                return self.data.sub_shapes
            else:
                return self.sub_shapes

        def add_shape(self, triangles, normals, vertices, layer = 0, material = 0):
            """Pack the given geometry."""
            # add the shape data
            if not self.data:
                self.data = NifFormat.hkPackedNiTriStripsData()
            data = self.data
            # increase number of shapes
            num_shapes = self.num_sub_shapes
            self.num_sub_shapes = num_shapes + 1
            self.sub_shapes.update_size()
            data.num_sub_shapes = num_shapes + 1
            data.sub_shapes.update_size()
            # add the shape
            self.sub_shapes[num_shapes].layer = layer
            self.sub_shapes[num_shapes].num_vertices = len(vertices)
            self.sub_shapes[num_shapes].material = material
            data.sub_shapes[num_shapes].layer = layer
            data.sub_shapes[num_shapes].num_vertices = len(vertices)
            data.sub_shapes[num_shapes].material = material
            firsttriangle = data.num_triangles
            firstvertex = data.num_vertices
            data.num_triangles += len(triangles)
            data.triangles.update_size()
            for tdata, t, n in zip(data.triangles[firsttriangle:], triangles, normals):
                tdata.triangle.v_1 = t[0] + firstvertex
                tdata.triangle.v_2 = t[1] + firstvertex
                tdata.triangle.v_3 = t[2] + firstvertex
                tdata.normal.x = n[0]
                tdata.normal.y = n[1]
                tdata.normal.z = n[2]
            data.num_vertices += len(vertices)
            data.vertices.update_size()
            for vdata, v in zip(data.vertices[firstvertex:], vertices):
                vdata.x = v[0] / 7.0
                vdata.y = v[1] / 7.0
                vdata.z = v[2] / 7.0
                
        def get_vertex_hash_generator(
            self,
            vertexprecision=3, subshape_index=None):
            """Generator which produces a tuple of integers for each
            vertex to ease detection of duplicate/close enough to remove
            vertices. The precision parameter denote number of
            significant digits behind the comma.

            For vertexprecision, 3 seems usually enough (maybe we'll
            have to increase this at some point).

            >>> shape = NifFormat.bhkPackedNiTriStripsShape()
            >>> data = NifFormat.hkPackedNiTriStripsData()
            >>> shape.data = data
            >>> shape.num_sub_shapes = 2
            >>> shape.sub_shapes.update_size()
            >>> data.num_vertices = 3
            >>> shape.sub_shapes[0].num_vertices = 2
            >>> shape.sub_shapes[1].num_vertices = 1
            >>> data.vertices.update_size()
            >>> data.vertices[0].x = 0.0
            >>> data.vertices[0].y = 0.1
            >>> data.vertices[0].z = 0.2
            >>> data.vertices[1].x = 1.0
            >>> data.vertices[1].y = 1.1
            >>> data.vertices[1].z = 1.2
            >>> data.vertices[2].x = 2.0
            >>> data.vertices[2].y = 2.1
            >>> data.vertices[2].z = 2.2
            >>> list(shape.get_vertex_hash_generator())
            [(0, (0, 100, 200)), (0, (1000, 1100, 1200)), (1, (2000, 2100, 2200))]
            >>> list(shape.get_vertex_hash_generator(subshape_index=0))
            [(0, 100, 200), (1000, 1100, 1200)]
            >>> list(shape.get_vertex_hash_generator(subshape_index=1))
            [(2000, 2100, 2200)]

            :param vertexprecision: Precision to be used for vertices.
            :type vertexprecision: float
            :return: A generator yielding a hash value for each vertex.
            """
            vertexfactor = 10 ** vertexprecision
            if subshape_index is None:
                for matid, vert in izip(chain(*[repeat(i, sub_shape.num_vertices)
                                                for i, sub_shape
                                                in enumerate(self.get_sub_shapes())]),
                                        self.data.vertices):
                    yield (matid, tuple(float_to_int(value * vertexfactor)
                                        for value in vert.as_list()))
            else:
                first_vertex = 0
                for i, subshape in izip(xrange(subshape_index),
                                        self.get_sub_shapes()):
                    first_vertex += subshape.num_vertices
                for vert_index in xrange(
                    first_vertex,
                    first_vertex
                    + self.get_sub_shapes()[subshape_index].num_vertices):
                    yield tuple(float_to_int(value * vertexfactor)
                                for value
                                in self.data.vertices[vert_index].as_list())

        def get_triangle_hash_generator(self):
            """Generator which produces a tuple of integers, or None
            in degenerate case, for each triangle to ease detection of
            duplicate triangles.

            >>> shape = NifFormat.bhkPackedNiTriStripsShape()
            >>> data = NifFormat.hkPackedNiTriStripsData()
            >>> shape.data = data
            >>> data.num_triangles = 6
            >>> data.triangles.update_size()
            >>> data.triangles[0].triangle.v_1 = 0
            >>> data.triangles[0].triangle.v_2 = 1
            >>> data.triangles[0].triangle.v_3 = 2
            >>> data.triangles[1].triangle.v_1 = 2
            >>> data.triangles[1].triangle.v_2 = 1
            >>> data.triangles[1].triangle.v_3 = 3
            >>> data.triangles[2].triangle.v_1 = 3
            >>> data.triangles[2].triangle.v_2 = 2
            >>> data.triangles[2].triangle.v_3 = 1
            >>> data.triangles[3].triangle.v_1 = 3
            >>> data.triangles[3].triangle.v_2 = 1
            >>> data.triangles[3].triangle.v_3 = 2
            >>> data.triangles[4].triangle.v_1 = 0
            >>> data.triangles[4].triangle.v_2 = 0
            >>> data.triangles[4].triangle.v_3 = 3
            >>> data.triangles[5].triangle.v_1 = 1
            >>> data.triangles[5].triangle.v_2 = 3
            >>> data.triangles[5].triangle.v_3 = 4
            >>> list(shape.get_triangle_hash_generator())
            [(0, 1, 2), (1, 3, 2), (1, 3, 2), (1, 2, 3), None, (1, 3, 4)]

            :return: A generator yielding a hash value for each triangle.
            """
            for tri in self.data.triangles:
                v_1, v_2, v_3 = tri.triangle.v_1, tri.triangle.v_2, tri.triangle.v_3
                if v_1 == v_2 or v_2 == v_3 or v_3 == v_1:
                    # degenerate
                    yield None
                elif v_1 < v_2 and v_1 < v_3:
                    # v_1 smallest
                    yield v_1, v_2, v_3
                elif v_2 < v_1 and v_2 < v_3:
                    # v_2 smallest
                    yield v_2, v_3, v_1
                else:
                    # v_3 smallest
                    yield v_3, v_1, v_2

    class bhkRagdollConstraint:
        def apply_scale(self, scale):
            """Scale data."""
            # apply scale on transform
            self.ragdoll.pivot_a.x *= scale
            self.ragdoll.pivot_a.y *= scale
            self.ragdoll.pivot_a.z *= scale
            self.ragdoll.pivot_b.x *= scale
            self.ragdoll.pivot_b.y *= scale
            self.ragdoll.pivot_b.z *= scale

        def update_a_b(self, parent):
            """Update the B data from the A data."""
            self.ragdoll.update_a_b(self.get_transform_a_b(parent))

    class bhkRefObject:
        def get_shape_mass_center_inertia(self, density=1, solid=True):
            """Return mass, center of gravity, and inertia tensor of
            this object's shape, if self.shape is not None.

            If self.shape is None, then returns zeros for everything.
            """
            if not self.shape:
                mass = 0
                center = (0, 0, 0)
                inertia = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
            else:
                mass, center, inertia = self.shape.get_mass_center_inertia(
                    density=density, solid=solid)
            return mass, center, inertia

    class bhkRigidBody:
        def apply_scale(self, scale):
            """Apply scale factor <scale> on data."""
            # apply scale on transform
            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale

            # apply scale on center of gravity
            self.center.x *= scale
            self.center.y *= scale
            self.center.z *= scale

            # apply scale on inertia tensor
            self.inertia.m_11 *= (scale ** 2)
            self.inertia.m_12 *= (scale ** 2)
            self.inertia.m_13 *= (scale ** 2)
            self.inertia.m_14 *= (scale ** 2)
            self.inertia.m_21 *= (scale ** 2)
            self.inertia.m_22 *= (scale ** 2)
            self.inertia.m_23 *= (scale ** 2)
            self.inertia.m_24 *= (scale ** 2)
            self.inertia.m_31 *= (scale ** 2)
            self.inertia.m_32 *= (scale ** 2)
            self.inertia.m_33 *= (scale ** 2)
            self.inertia.m_34 *= (scale ** 2)

        def update_mass_center_inertia(self, density=1, solid=True, mass=None):
            """Look at all the objects under this rigid body and update the mass,
            center of gravity, and inertia tensor accordingly. If the C{mass} parameter
            is given then the C{density} argument is ignored."""
            if not mass is None:
                density = 1

            calc_mass, center, inertia = self.get_shape_mass_center_inertia(
                density=density, solid=solid)

            self.mass = calc_mass
            self.center.x, self.center.y, self.center.z = center
            self.inertia.m_11 = inertia[0][0]
            self.inertia.m_12 = inertia[0][1]
            self.inertia.m_13 = inertia[0][2]
            self.inertia.m_14 = 0
            self.inertia.m_21 = inertia[1][0]
            self.inertia.m_22 = inertia[1][1]
            self.inertia.m_23 = inertia[1][2]
            self.inertia.m_24 = 0
            self.inertia.m_31 = inertia[2][0]
            self.inertia.m_32 = inertia[2][1]
            self.inertia.m_33 = inertia[2][2]
            self.inertia.m_34 = 0

            if not mass is None:
                mass_correction = mass / calc_mass if calc_mass != 0 else 1
                self.mass = mass
                self.inertia.m_11 *= mass_correction
                self.inertia.m_12 *= mass_correction
                self.inertia.m_13 *= mass_correction
                self.inertia.m_14 *= mass_correction
                self.inertia.m_21 *= mass_correction
                self.inertia.m_22 *= mass_correction
                self.inertia.m_23 *= mass_correction
                self.inertia.m_24 *= mass_correction
                self.inertia.m_31 *= mass_correction
                self.inertia.m_32 *= mass_correction
                self.inertia.m_33 *= mass_correction
                self.inertia.m_34 *= mass_correction

    class bhkSphereShape:
        def apply_scale(self, scale):
            """Apply scale factor <scale> on data."""
            # apply scale on dimensions
            self.radius *= scale

        def get_mass_center_inertia(self, density = 1, solid = True):
            """Return mass, center, and inertia tensor."""
            # the dimensions describe half the size of the box in each dimension
            # so the length of a single edge is dimension.dir * 2
            mass, inertia = pyffi.utils.inertia.getMassInertiaSphere(
                self.radius, density = density, solid = solid)
            return mass, (0,0,0), inertia

    class bhkTransformShape:
        def apply_scale(self, scale):
            """Apply scale factor <scale> on data."""
            # apply scale on translation
            self.transform.m_14 *= scale
            self.transform.m_24 *= scale
            self.transform.m_34 *= scale

        def get_mass_center_inertia(self, density=1, solid=True):
            """Return mass, center, and inertia tensor."""
            # get shape mass, center, and inertia
            mass, center, inertia = self.get_shape_mass_center_inertia(
                density=density, solid=solid)
            # get transform matrix and translation vector
            transform = self.transform.get_matrix_33().as_tuple()
            transform_transposed = matTransposed(transform)
            translation = ( self.transform.m_14, self.transform.m_24, self.transform.m_34 )
            # transform center and inertia
            center = matvecMul(transform, center)
            center = vecAdd(center, translation)
            inertia = matMul(matMul(transform_transposed, inertia), transform)
            # return updated mass center and inertia
            return mass, center, inertia

    class BSBound:
        def apply_scale(self, scale):
            """Scale data."""
            self.center.x *= scale
            self.center.y *= scale
            self.center.z *= scale
            self.dimensions.x *= scale
            self.dimensions.y *= scale
            self.dimensions.z *= scale

    class BSDismemberSkinInstance:
        def get_dismember_partitions(self):
            """Return triangles and body part indices."""
            triangles = []
            trianglepartmap = []
            for bodypart, skinpartblock in zip(
                self.partitions, self.skin_partition.skin_partition_blocks):
                part_triangles = list(skinpartblock.get_mapped_triangles())
                triangles += part_triangles
                trianglepartmap += [bodypart.body_part] * len(part_triangles)
            return triangles, trianglepartmap

    class ControllerLink:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> link = NifFormat.ControllerLink()
        >>> link.node_name_offset
        -1
        >>> link.set_node_name("Bip01")
        >>> link.node_name_offset
        0
        >>> link.get_node_name()
        'Bip01'
        >>> link.node_name
        'Bip01'
        >>> link.set_node_name("Bip01 Tail")
        >>> link.node_name_offset
        6
        >>> link.get_node_name()
        'Bip01 Tail'
        >>> link.node_name
        'Bip01 Tail'
        """
        def _get_string(self, offset):
            """A wrapper around string_palette.palette.get_string. Used by get_node_name
            etc. Returns the string at given offset."""
            if offset == -1:
                return ''

            if not self.string_palette:
                return ''

            return self.string_palette.palette.get_string(offset)

        def _add_string(self, text):
            """Wrapper for string_palette.palette.add_string. Used by set_node_name etc.
            Returns offset of string added."""
            # create string palette if none exists yet
            if not self.string_palette:
                self.string_palette = NifFormat.NiStringPalette()
            # add the string and return the offset
            return self.string_palette.palette.add_string(text)

        def get_node_name(self):
            """Return the node name.

            >>> # a doctest
            >>> from pyffi.formats.nif import NifFormat
            >>> link = NifFormat.ControllerLink()
            >>> link.string_palette = NifFormat.NiStringPalette()
            >>> palette = link.string_palette.palette
            >>> link.node_name_offset = palette.add_string("Bip01")
            >>> link.get_node_name()
            'Bip01'

            >>> # another doctest
            >>> from pyffi.formats.nif import NifFormat
            >>> link = NifFormat.ControllerLink()
            >>> link.node_name = "Bip01"
            >>> link.get_node_name()
            'Bip01'
            """
            if self.node_name:
                return self.node_name
            else:
                return self._get_string(self.node_name_offset)

        def set_node_name(self, text):
            self.node_name = text
            self.node_name_offset = self._add_string(text)

        def get_property_type(self):
            if self.property_type:
                return self.property_type
            else:
                return self._get_string(self.property_type_offset)

        def set_property_type(self, text):
            self.property_type = text
            self.property_type_offset = self._add_string(text)

        def get_controller_type(self):
            if self.controller_type:
                return self.controller_type
            else:
                return self._get_string(self.controller_type_offset)

        def set_controller_type(self, text):
            self.controller_type = text
            self.controller_type_offset = self._add_string(text)

        def get_variable_1(self):
            if self.variable_1:
                return self.variable_1
            else:
                return self._get_string(self.variable_1_offset)

        def set_variable_1(self, text):
            self.variable_1 = text
            self.variable_1_offset = self._add_string(text)

        def get_variable_2(self):
            if self.variable_2:
                return self.variable_2
            else:
                return self._get_string(self.variable_2_offset)

        def set_variable_2(self, text):
            self.variable_2 = text
            self.variable_2_offset = self._add_string(text)

    class hkPackedNiTriStripsData:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < NifFormat.EPSILON:
                return
            for vert in self.vertices:
                vert.x *= scale
                vert.y *= scale
                vert.z *= scale

    class InertiaMatrix:
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
                "[ %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f ]\n"
                % (self.m_11, self.m_12, self.m_13,
                   self.m_21, self.m_22, self.m_23,
                   self.m_31, self.m_32, self.m_33))

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

        def is_identity(self):
            """Return ``True`` if the matrix is close to identity."""
            if  (abs(self.m_11 - 1.0) > NifFormat.EPSILON
                 or abs(self.m_12) > NifFormat.EPSILON
                 or abs(self.m_13) > NifFormat.EPSILON
                 or abs(self.m_21) > NifFormat.EPSILON
                 or abs(self.m_22 - 1.0) > NifFormat.EPSILON
                 or abs(self.m_23) > NifFormat.EPSILON
                 or abs(self.m_31) > NifFormat.EPSILON
                 or abs(self.m_32) > NifFormat.EPSILON
                 or abs(self.m_33 - 1.0) > NifFormat.EPSILON):
                return False
            else:
                return True

        def get_copy(self):
            """Return a copy of the matrix."""
            mat = NifFormat.InertiaMatrix()
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
            return mat

        def __eq__(self, mat):
            if not isinstance(mat, NifFormat.InertiaMatrix):
                raise TypeError(
                    "do not know how to compare InertiaMatrix and %s"%mat.__class__)
            if (abs(self.m_11 - mat.m_11) > NifFormat.EPSILON
                or abs(self.m_12 - mat.m_12) > NifFormat.EPSILON
                or abs(self.m_13 - mat.m_13) > NifFormat.EPSILON
                or abs(self.m_21 - mat.m_21) > NifFormat.EPSILON
                or abs(self.m_22 - mat.m_22) > NifFormat.EPSILON
                or abs(self.m_23 - mat.m_23) > NifFormat.EPSILON
                or abs(self.m_31 - mat.m_31) > NifFormat.EPSILON
                or abs(self.m_32 - mat.m_32) > NifFormat.EPSILON
                or abs(self.m_33 - mat.m_33) > NifFormat.EPSILON):
                return False
            return True

        def __ne__(self, mat):
            return not self.__eq__(mat)

    class LimitedHingeDescriptor:
        def update_a_b(self, transform):
            """Update B pivot and axes from A using the given transform."""
            # pivot point
            pivot_b = ((7 * self.pivot_a.get_vector_3()) * transform) / 7.0
            self.pivot_b.x = pivot_b.x
            self.pivot_b.y = pivot_b.y
            self.pivot_b.z = pivot_b.z
            # axes (rotation only)
            transform = transform.get_matrix_33()
            axle_b = self.axle_a.get_vector_3() *  transform
            perp_2_axle_in_b_2 = self.perp_2_axle_in_a_2.get_vector_3() * transform
            self.axle_b.x = axle_b.x
            self.axle_b.y = axle_b.y
            self.axle_b.z = axle_b.z
            self.perp_2_axle_in_b_2.x = perp_2_axle_in_b_2.x
            self.perp_2_axle_in_b_2.y = perp_2_axle_in_b_2.y
            self.perp_2_axle_in_b_2.z = perp_2_axle_in_b_2.z

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
                "[ %6.3f %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f %6.3f ]\n"
                "[ %6.3f %6.3f %6.3f %6.3f ]\n"
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
            if (abs(self.m_11 - 1.0) > NifFormat.EPSILON
                or abs(self.m_12) > NifFormat.EPSILON
                or abs(self.m_13) > NifFormat.EPSILON
                or abs(self.m_14) > NifFormat.EPSILON
                or abs(self.m_21) > NifFormat.EPSILON
                or abs(self.m_22 - 1.0) > NifFormat.EPSILON
                or abs(self.m_23) > NifFormat.EPSILON
                or abs(self.m_24) > NifFormat.EPSILON
                or abs(self.m_31) > NifFormat.EPSILON
                or abs(self.m_32) > NifFormat.EPSILON
                or abs(self.m_33 - 1.0) > NifFormat.EPSILON
                or abs(self.m_34) > NifFormat.EPSILON
                or abs(self.m_41) > NifFormat.EPSILON
                or abs(self.m_42) > NifFormat.EPSILON
                or abs(self.m_43) > NifFormat.EPSILON
                or abs(self.m_44 - 1.0) > NifFormat.EPSILON):
                return False
            else:
                return True

        def get_copy(self):
            """Create a copy of the matrix."""
            mat = NifFormat.Matrix44()
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
            m = NifFormat.Matrix33()
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
            if not isinstance(m, NifFormat.Matrix33):
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
            t = NifFormat.Vector3()
            t.x = self.m_41
            t.y = self.m_42
            t.z = self.m_43
            return t

        def set_translation(self, translation):
            """Returns lower left 1x3 part."""
            if not isinstance(translation, NifFormat.Vector3):
                raise TypeError('argument must be Vector3')
            self.m_41 = translation.x
            self.m_42 = translation.y
            self.m_43 = translation.z

        def is_scale_rotation_translation(self):
            if not self.get_matrix_33().is_scale_rotation(): return False
            if abs(self.m_14) > NifFormat.EPSILON: return False
            if abs(self.m_24) > NifFormat.EPSILON: return False
            if abs(self.m_34) > NifFormat.EPSILON: return False
            if abs(self.m_44 - 1.0) > NifFormat.EPSILON: return False
            return True

        def get_scale_rotation_translation(self):
            rotscl = self.get_matrix_33()
            scale = rotscl.get_scale()
            rot = rotscl / scale
            trans = self.get_translation()
            return (scale, rot, trans)

        def get_scale_quat_translation(self):
            rotscl = self.get_matrix_33()
            scale, quat = rotscl.get_scale_quat()
            trans = self.get_translation()
            return (scale, quat, trans)

        def set_scale_rotation_translation(self, scale, rotation, translation):
            if not isinstance(scale, (float, int, long)):
                raise TypeError('scale must be float')
            if not isinstance(rotation, NifFormat.Matrix33):
                raise TypeError('rotation must be Matrix33')
            if not isinstance(translation, NifFormat.Vector3):
                raise TypeError('translation must be Vector3')

            if not rotation.is_rotation():
                logger = logging.getLogger("pyffi.nif.matrix")
                mat = rotation * rotation.get_transpose()
                idmat = NifFormat.Matrix33()
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

                n = NifFormat.Matrix44()
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
                if abs(det) < NifFormat.EPSILON:
                    raise ZeroDivisionError('cannot invert matrix:\n%s'%self)
                for i in xrange(4):
                    for j in xrange(4):
                        if (i+j) & 1:
                            nn[j][i] = -determinant(adjoint(m, i, j)) / det
                        else:
                            nn[j][i] = determinant(adjoint(m, i, j)) / det
                n = NifFormat.Matrix44()
                n.set_rows(*nn)
                return n

        def __mul__(self, x):
            if isinstance(x, (float, int, long)):
                m = NifFormat.Matrix44()
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
            elif isinstance(x, NifFormat.Vector3):
                raise TypeError("matrix*vector not supported; please use left multiplication (vector*matrix)")
            elif isinstance(x, NifFormat.Vector4):
                raise TypeError("matrix*vector not supported; please use left multiplication (vector*matrix)")
            elif isinstance(x, NifFormat.Matrix44):
                m = NifFormat.Matrix44()
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
                m = NifFormat.Matrix44()
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

        # py3k
        __truediv__ = __div__

        def __rmul__(self, x):
            if isinstance(x, (float, int, long)):
                return self * x
            else:
                raise TypeError("do not know how to multiply %s with Matrix44"%x.__class__)

        def __eq__(self, m):
            if isinstance(m, type(None)):
                return False
            if not isinstance(m, NifFormat.Matrix44):
                raise TypeError("do not know how to compare Matrix44 and %s"%m.__class__)
            if abs(self.m_11 - m.m_11) > NifFormat.EPSILON: return False
            if abs(self.m_12 - m.m_12) > NifFormat.EPSILON: return False
            if abs(self.m_13 - m.m_13) > NifFormat.EPSILON: return False
            if abs(self.m_14 - m.m_14) > NifFormat.EPSILON: return False
            if abs(self.m_21 - m.m_21) > NifFormat.EPSILON: return False
            if abs(self.m_22 - m.m_22) > NifFormat.EPSILON: return False
            if abs(self.m_23 - m.m_23) > NifFormat.EPSILON: return False
            if abs(self.m_24 - m.m_24) > NifFormat.EPSILON: return False
            if abs(self.m_31 - m.m_31) > NifFormat.EPSILON: return False
            if abs(self.m_32 - m.m_32) > NifFormat.EPSILON: return False
            if abs(self.m_33 - m.m_33) > NifFormat.EPSILON: return False
            if abs(self.m_34 - m.m_34) > NifFormat.EPSILON: return False
            if abs(self.m_41 - m.m_41) > NifFormat.EPSILON: return False
            if abs(self.m_42 - m.m_42) > NifFormat.EPSILON: return False
            if abs(self.m_43 - m.m_43) > NifFormat.EPSILON: return False
            if abs(self.m_44 - m.m_44) > NifFormat.EPSILON: return False
            return True

        def __ne__(self, m):
            return not self.__eq__(m)

        def __add__(self, x):
            if isinstance(x, (NifFormat.Matrix44)):
                m = NifFormat.Matrix44()
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
                m = NifFormat.Matrix44()
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
            if isinstance(x, (NifFormat.Matrix44)):
                m = NifFormat.Matrix44()
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
                m = NifFormat.Matrix44()
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

    class NiAVObject:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> node = NifFormat.NiNode()
        >>> prop1 = NifFormat.NiProperty()
        >>> prop1.name = "hello"
        >>> prop2 = NifFormat.NiProperty()
        >>> prop2.name = "world"
        >>> node.get_properties()
        []
        >>> node.set_properties([prop1, prop2])
        >>> [prop.name for prop in node.get_properties()]
        ['hello', 'world']
        >>> [prop.name for prop in node.properties]
        ['hello', 'world']
        >>> node.set_properties([])
        >>> node.get_properties()
        []
        >>> # now set them the other way around
        >>> node.set_properties([prop2, prop1])
        >>> [prop.name for prop in node.get_properties()]
        ['world', 'hello']
        >>> [prop.name for prop in node.properties]
        ['world', 'hello']
        >>> node.remove_property(prop2)
        >>> [prop.name for prop in node.properties]
        ['hello']
        >>> node.add_property(prop2)
        >>> [prop.name for prop in node.properties]
        ['hello', 'world']
        """
        def add_property(self, prop):
            """Add the given property to the property list.

            :param prop: The property block to add.
            :type prop: L{NifFormat.NiProperty}
            """
            num_props = self.num_properties
            self.num_properties = num_props + 1
            self.properties.update_size()
            self.properties[num_props] = prop

        def remove_property(self, prop):
            """Remove the given property to the property list.

            :param prop: The property block to remove.
            :type prop: L{NifFormat.NiProperty}
            """
            self.set_properties([otherprop for otherprop in self.get_properties()
                                if not(otherprop is prop)])

        def get_properties(self):
            """Return a list of the properties of the block.

            :return: The list of properties.
            :rtype: ``list`` of L{NifFormat.NiProperty}
            """
            return [prop for prop in self.properties]

        def set_properties(self, proplist):
            """Set the list of properties from the given list (destroys existing list).

            :param proplist: The list of property blocks to set.
            :type proplist: ``list`` of L{NifFormat.NiProperty}
            """
            self.num_properties = len(proplist)
            self.properties.update_size()
            for i, prop in enumerate(proplist):
                self.properties[i] = prop

        def get_transform(self, relative_to=None):
            """Return scale, rotation, and translation into a single 4x4
            matrix, relative to the C{relative_to} block (which should be
            another NiAVObject connecting to this block). If C{relative_to} is
            ``None``, then returns the transform stored in C{self}, or
            equivalently, the target is assumed to be the parent.

            :param relative_to: The block relative to which the transform must
                be calculated. If ``None``, the local transform is returned.
            """
            m = NifFormat.Matrix44()
            m.set_scale_rotation_translation(self.scale, self.rotation, self.translation)
            if not relative_to: return m
            # find chain from relative_to to self
            chain = relative_to.find_chain(self, block_type = NifFormat.NiAVObject)
            if not chain:
                raise ValueError(
                    'cannot find a chain of NiAVObject blocks '
                    'between %s and %s.' % (self.name, relative_to.name))
            # and multiply with all transform matrices (not including relative_to)
            for block in reversed(chain[1:-1]):
                m *= block.get_transform()
            return m

        def set_transform(self, m):
            """Set rotation, translation, and scale, from a 4x4 matrix.

            :param m: The matrix to which the transform should be set."""
            scale, rotation, translation = m.get_scale_rotation_translation()

            self.scale = scale

            self.rotation.m_11 = rotation.m_11
            self.rotation.m_12 = rotation.m_12
            self.rotation.m_13 = rotation.m_13
            self.rotation.m_21 = rotation.m_21
            self.rotation.m_22 = rotation.m_22
            self.rotation.m_23 = rotation.m_23
            self.rotation.m_31 = rotation.m_31
            self.rotation.m_32 = rotation.m_32
            self.rotation.m_33 = rotation.m_33

            self.translation.x = translation.x
            self.translation.y = translation.y
            self.translation.z = translation.z

        def apply_scale(self, scale):
            """Apply scale factor on data.

            :param scale: The scale factor."""
            # apply scale on translation
            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale
            # apply scale on bounding box
            self.bounding_box.translation.x *= scale
            self.bounding_box.translation.y *= scale
            self.bounding_box.translation.z *= scale
            self.bounding_box.radius.x *= scale
            self.bounding_box.radius.y *= scale
            self.bounding_box.radius.z *= scale

    class NiBSplineCompTransformInterpolator:
        def get_translations(self):
            """Return an iterator over all translation keys."""
            return self._getCompKeys(self.translation_offset, 3,
                                     self.translation_bias, self.translation_multiplier)

        def get_rotations(self):
            """Return an iterator over all rotation keys."""
            return self._getCompKeys(self.rotation_offset, 4,
                                     self.rotation_bias, self.rotation_multiplier)

        def get_scales(self):
            """Return an iterator over all scale keys."""
            for key in self._getCompKeys(self.scale_offset, 1,
                                         self.scale_bias, self.scale_multiplier):
                yield key[0]

        def apply_scale(self, scale):
            """Apply scale factor on data."""
            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale
            self.translation_bias *= scale
            self.translation_multiplier *= scale

    class NiBSplineData:
        """
        >>> # a doctest
        >>> from pyffi.formats.nif import NifFormat
        >>> block = NifFormat.NiBSplineData()
        >>> block.num_short_control_points = 50
        >>> block.short_control_points.update_size()
        >>> for i in range(block.num_short_control_points):
        ...     block.short_control_points[i] = 20 - i
        >>> list(block.get_short_data(12, 4, 3))
        [(8, 7, 6), (5, 4, 3), (2, 1, 0), (-1, -2, -3)]
        >>> offset = block.append_short_data([(1,2),(4,3),(13,14),(8,2),(33,33)])
        >>> offset
        50
        >>> list(block.get_short_data(offset, 5, 2))
        [(1, 2), (4, 3), (13, 14), (8, 2), (33, 33)]
        >>> list(block.get_comp_data(offset, 5, 2, 10.0, 32767.0))
        [(11.0, 12.0), (14.0, 13.0), (23.0, 24.0), (18.0, 12.0), (43.0, 43.0)]
        >>> block.append_float_data([(1.0,2.0),(3.0,4.0),(0.5,0.25)])
        0
        >>> list(block.get_float_data(0, 3, 2))
        [(1.0, 2.0), (3.0, 4.0), (0.5, 0.25)]
        >>> block.append_comp_data([(1,2),(4,3)])
        (60, 2.5, 1.5)
        >>> list(block.get_short_data(60, 2, 2))
        [(-32767, -10922), (32767, 10922)]
        >>> list(block.get_comp_data(60, 2, 2, 2.5, 1.5)) # doctest: +ELLIPSIS
        [(1.0, 2.00...), (4.0, 2.99...)]
        """
        def _getData(self, offset, num_elements, element_size, controlpoints):
            """Helper function for get_float_data and get_short_data. For internal
            use only."""
            # check arguments
            if not (controlpoints is self.float_control_points
                    or controlpoints is self.short_control_points):
                raise ValueError("internal error while appending data")
            # parse the data
            for element in xrange(num_elements):
                yield tuple(
                    controlpoints[offset + element * element_size + index]
                    for index in xrange(element_size))

        def _appendData(self, data, controlpoints):
            """Helper function for append_float_data and append_short_data. For internal
            use only."""
            # get number of elements
            num_elements = len(data)
            # empty list, do nothing
            if num_elements == 0:
                return
            # get element size
            element_size = len(data[0])
            # store offset at which we append the data
            if controlpoints is self.float_control_points:
                offset = self.num_float_control_points
                self.num_float_control_points += num_elements * element_size
            elif controlpoints is self.short_control_points:
                offset = self.num_short_control_points
                self.num_short_control_points += num_elements * element_size
            else:
                raise ValueError("internal error while appending data")
            # update size
            controlpoints.update_size()
            # store the data
            for element, datum in enumerate(data):
                for index, value in enumerate(datum):
                    controlpoints[offset + element * element_size + index] = value
            # return the offset
            return offset

        def get_short_data(self, offset, num_elements, element_size):
            """Get an iterator to the data.

            :param offset: The offset in the data where to start.
            :param num_elements: Number of elements to get.
            :param element_size: Size of a single element.
            :return: A list of C{num_elements} tuples of size C{element_size}.
            """
            return self._getData(
                offset, num_elements, element_size, self.short_control_points)

        def get_comp_data(self, offset, num_elements, element_size, bias, multiplier):
            """Get an interator to the data, converted to float with extra bias and
            multiplication factor. If C{x} is the short value, then the returned value
            is C{bias + x * multiplier / 32767.0}.

            :param offset: The offset in the data where to start.
            :param num_elements: Number of elements to get.
            :param element_size: Size of a single element.
            :param bias: Value bias.
            :param multiplier: Value multiplier.
            :return: A list of C{num_elements} tuples of size C{element_size}.
            """
            for key in self.get_short_data(offset, num_elements, element_size):
                yield tuple(bias + x * multiplier / 32767.0 for x in key)

        def append_short_data(self, data):
            """Append data.

            :param data: A list of elements, where each element is a tuple of
                integers. (Note: cannot be an interator; maybe this restriction
                will be removed in a future version.)
            :return: The offset at which the data was appended."""
            return self._appendData(data, self.short_control_points)

        def append_comp_data(self, data):
            """Append data as compressed list.

            :param data: A list of elements, where each element is a tuple of
                integers. (Note: cannot be an interator; maybe this restriction
                will be removed in a future version.)
            :return: The offset, bias, and multiplier."""
            # get extremes
            maxvalue = max(max(datum) for datum in data)
            minvalue = min(min(datum) for datum in data)
            # get bias and multiplier
            bias = 0.5 * (maxvalue + minvalue)
            if maxvalue > minvalue:
                multiplier = 0.5 * (maxvalue - minvalue)
            else:
                # no need to compress in this case
                multiplier = 1.0

            # compress points into shorts
            shortdata = []
            for datum in data:
                shortdata.append(tuple(int(32767 * (x - bias) / multiplier)
                                       for x in datum))
            return (self._appendData(shortdata, self.short_control_points),
                    bias, multiplier)

        def get_float_data(self, offset, num_elements, element_size):
            """Get an iterator to the data.

            :param offset: The offset in the data where to start.
            :param num_elements: Number of elements to get.
            :param element_size: Size of a single element.
            :return: A list of C{num_elements} tuples of size C{element_size}.
            """
            return self._getData(
                offset, num_elements, element_size, self.float_control_points)

        def append_float_data(self, data):
            """Append data.

            :param data: A list of elements, where each element is a tuple of
                floats. (Note: cannot be an interator; maybe this restriction
                will be removed in a future version.)
            :return: The offset at which the data was appended."""
            return self._appendData(data, self.float_control_points)

    class NiBSplineInterpolator:
        def get_times(self):
            """Return an iterator over all key times.

            @todo: When code for calculating the bsplines is ready, this function
            will return exactly self.basis_data.num_control_points - 1 time points, and
            not self.basis_data.num_control_points as it is now.
            """
            # is there basis data?
            if not self.basis_data:
                return
            # return all times
            for i in xrange(self.basis_data.num_control_points):
                yield (
                    self.start_time
                    + (i * (self.stop_time - self.start_time)
                       / (self.basis_data.num_control_points - 1))
                    )

        def _getFloatKeys(self, offset, element_size):
            """Helper function to get iterator to various keys. Internal use only."""
            # are there keys?
            if offset == 65535:
                return
            # is there basis data and spline data?
            if not self.basis_data or not self.spline_data:
                return
            # yield all keys
            for key in self.spline_data.get_float_data(offset,
                                                    self.basis_data.num_control_points,
                                                    element_size):
                yield key

        def _getCompKeys(self, offset, element_size, bias, multiplier):
            """Helper function to get iterator to various keys. Internal use only."""
            # are there keys?
            if offset == 65535:
                return
            # is there basis data and spline data?
            if not self.basis_data or not self.spline_data:
                return
            # yield all keys
            for key in self.spline_data.get_comp_data(offset,
                                                   self.basis_data.num_control_points,
                                                   element_size,
                                                   bias, multiplier):
                yield key

    class NiBSplineTransformInterpolator:
        def get_translations(self):
            """Return an iterator over all translation keys."""
            return self._getFloatKeys(self.translation_offset, 3)

        def get_rotations(self):
            """Return an iterator over all rotation keys."""
            return self._getFloatKeys(self.rotation_offset, 4)

        def get_scales(self):
            """Return an iterator over all scale keys."""
            for key in self._getFloatKeys(self.scale_offset, 1):
                yield key[0]

        def apply_scale(self, scale):
            """Apply scale factor on data."""
            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale
            # also scale translation float keys
            if self.translation_offset != 65535:
                offset = self.translation_offset
                num_elements = self.basis_data.num_control_points
                element_size = 3
                controlpoints = self.spline_data.float_control_points
                for element in xrange(num_elements):
                    for index in xrange(element_size):
                        controlpoints[offset + element * element_size + index] *= scale

    class NiControllerSequence:
        def add_controlled_block(self):
            """Create new controlled block, and return it.

            >>> seq = NifFormat.NiControllerSequence()
            >>> seq.num_controlled_blocks
            0
            >>> ctrlblock = seq.add_controlled_block()
            >>> seq.num_controlled_blocks
            1
            >>> isinstance(ctrlblock, NifFormat.ControllerLink)
            True
            """
            # add to the list
            num_blocks = self.num_controlled_blocks
            self.num_controlled_blocks = num_blocks + 1
            self.controlled_blocks.update_size()
            return self.controlled_blocks[-1]

    class NiGeometryData:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> geomdata = NifFormat.NiGeometryData()
        >>> geomdata.num_vertices = 3
        >>> geomdata.has_vertices = True
        >>> geomdata.has_normals = True
        >>> geomdata.has_vertex_colors = True
        >>> geomdata.num_uv_sets = 2
        >>> geomdata.vertices.update_size()
        >>> geomdata.normals.update_size()
        >>> geomdata.vertex_colors.update_size()
        >>> geomdata.uv_sets.update_size()
        >>> geomdata.vertices[0].x = 1
        >>> geomdata.vertices[0].y = 2
        >>> geomdata.vertices[0].z = 3
        >>> geomdata.vertices[1].x = 4
        >>> geomdata.vertices[1].y = 5
        >>> geomdata.vertices[1].z = 6
        >>> geomdata.vertices[2].x = 1.200001
        >>> geomdata.vertices[2].y = 3.400001
        >>> geomdata.vertices[2].z = 5.600001
        >>> geomdata.normals[0].x = 0
        >>> geomdata.normals[0].y = 0
        >>> geomdata.normals[0].z = 1
        >>> geomdata.normals[1].x = 0
        >>> geomdata.normals[1].y = 1
        >>> geomdata.normals[1].z = 0
        >>> geomdata.normals[2].x = 1
        >>> geomdata.normals[2].y = 0
        >>> geomdata.normals[2].z = 0
        >>> geomdata.vertex_colors[1].r = 0.310001
        >>> geomdata.vertex_colors[1].g = 0.320001
        >>> geomdata.vertex_colors[1].b = 0.330001
        >>> geomdata.vertex_colors[1].a = 0.340001
        >>> geomdata.uv_sets[0][0].u = 0.990001
        >>> geomdata.uv_sets[0][0].v = 0.980001
        >>> geomdata.uv_sets[0][2].u = 0.970001
        >>> geomdata.uv_sets[0][2].v = 0.960001
        >>> geomdata.uv_sets[1][0].v = 0.910001
        >>> geomdata.uv_sets[1][0].v = 0.920001
        >>> geomdata.uv_sets[1][2].v = 0.930001
        >>> geomdata.uv_sets[1][2].v = 0.940001
        >>> for h in geomdata.get_vertex_hash_generator():
        ...     print(h)
        (1000, 2000, 3000, 0, 0, 1000, 99000, 98000, 0, 92000, 0, 0, 0, 0)
        (4000, 5000, 6000, 0, 1000, 0, 0, 0, 0, 0, 310, 320, 330, 340)
        (1200, 3400, 5600, 1000, 0, 0, 97000, 96000, 0, 94000, 0, 0, 0, 0)
        """
        def update_center_radius(self):
            """Recalculate center and radius of the data."""
            # in case there are no vertices, set center and radius to zero
            if len(self.vertices) == 0:
                self.center.x = 0.0
                self.center.y = 0.0
                self.center.z = 0.0
                self.radius = 0.0
                return

            # find extreme values in x, y, and z direction
            lowx = min([v.x for v in self.vertices])
            lowy = min([v.y for v in self.vertices])
            lowz = min([v.z for v in self.vertices])
            highx = max([v.x for v in self.vertices])
            highy = max([v.y for v in self.vertices])
            highz = max([v.z for v in self.vertices])

            # center is in the center of the bounding box
            cx = (lowx + highx) * 0.5
            cy = (lowy + highy) * 0.5
            cz = (lowz + highz) * 0.5
            self.center.x = cx
            self.center.y = cy
            self.center.z = cz

            # radius is the largest distance from the center
            r2 = 0.0
            for v in self.vertices:
                dx = cx - v.x
                dy = cy - v.y
                dz = cz - v.z
                r2 = max(r2, dx*dx+dy*dy+dz*dz)
            self.radius = r2 ** 0.5

        def apply_scale(self, scale):
            """Apply scale factor on data."""
            if abs(scale - 1.0) < NifFormat.EPSILON: return
            for v in self.vertices:
                v.x *= scale
                v.y *= scale
                v.z *= scale
            self.center.x *= scale
            self.center.y *= scale
            self.center.z *= scale
            self.radius *= scale

        def get_vertex_hash_generator(
            self,
            vertexprecision=3, normalprecision=3,
            uvprecision=5, vcolprecision=3):
            """Generator which produces a tuple of integers for each
            (vertex, normal, uv, vcol), to ease detection of duplicate
            vertices. The precision parameters denote number of
            significant digits behind the comma.

            Default for uvprecision should really be high because for
            very large models the uv coordinates can be very close
            together.

            For vertexprecision, 3 seems usually enough (maybe we'll
            have to increase this at some point).

            :param vertexprecision: Precision to be used for vertices.
            :type vertexprecision: float
            :param normalprecision: Precision to be used for normals.
            :type normalprecision: float
            :param uvprecision: Precision to be used for uvs.
            :type uvprecision: float
            :param vcolprecision: Precision to be used for vertex colors.
            :type vcolprecision: float
            :return: A generator yielding a hash value for each vertex.
            """
            
            verts = self.vertices if self.has_vertices else None
            norms = self.normals if self.has_normals else None
            uvsets = self.uv_sets if len(self.uv_sets) else None
            vcols = self.vertex_colors if self.has_vertex_colors else None
            vertexfactor = 10 ** vertexprecision
            normalfactor = 10 ** normalprecision
            uvfactor = 10 ** uvprecision
            vcolfactor = 10 ** vcolprecision
            for i in xrange(self.num_vertices):
                h = []
                if verts:
                    h.extend([float_to_int(x * vertexfactor)
                             for x in [verts[i].x, verts[i].y, verts[i].z]])
                if norms:
                    h.extend([float_to_int(x * normalfactor)
                              for x in [norms[i].x, norms[i].y, norms[i].z]])
                if uvsets:
                    for uvset in uvsets:
                        # uvs sometimes have NaN, for example:
                        # oblivion/meshes/architecture/anvil/anvildooruc01.nif
                        h.extend([float_to_int(x * uvfactor)
                                  for x in [uvset[i].u, uvset[i].v]])
                if vcols:
                    h.extend([float_to_int(x * vcolfactor)
                              for x in [vcols[i].r, vcols[i].g,
                                        vcols[i].b, vcols[i].a]])
                yield tuple(h)

    class NiGeometry:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> id44 = NifFormat.Matrix44()
        >>> id44.set_identity()
        >>> skelroot = NifFormat.NiNode()
        >>> skelroot.name = 'skelroot'
        >>> skelroot.set_transform(id44)
        >>> bone1 = NifFormat.NiNode()
        >>> bone1.name = 'bone1'
        >>> bone1.set_transform(id44)
        >>> bone2 = NifFormat.NiNode()
        >>> bone2.name = 'bone2'
        >>> bone2.set_transform(id44)
        >>> bone21 = NifFormat.NiNode()
        >>> bone21.name = 'bone21'
        >>> bone21.set_transform(id44)
        >>> bone22 = NifFormat.NiNode()
        >>> bone22.name = 'bone22'
        >>> bone22.set_transform(id44)
        >>> bone211 = NifFormat.NiNode()
        >>> bone211.name = 'bone211'
        >>> bone211.set_transform(id44)
        >>> skelroot.add_child(bone1)
        >>> bone1.add_child(bone2)
        >>> bone2.add_child(bone21)
        >>> bone2.add_child(bone22)
        >>> bone21.add_child(bone211)
        >>> geom = NifFormat.NiTriShape()
        >>> geom.name = 'geom'
        >>> geom.set_transform(id44)
        >>> geomdata = NifFormat.NiTriShapeData()
        >>> skininst = NifFormat.NiSkinInstance()
        >>> skindata = NifFormat.NiSkinData()
        >>> skelroot.add_child(geom)
        >>> geom.data = geomdata
        >>> geom.skin_instance = skininst
        >>> skininst.skeleton_root = skelroot
        >>> skininst.data = skindata
        >>> skininst.num_bones = 4
        >>> skininst.bones.update_size()
        >>> skininst.bones[0] = bone1
        >>> skininst.bones[1] = bone2
        >>> skininst.bones[2] = bone22
        >>> skininst.bones[3] = bone211
        >>> skindata.num_bones = 4
        >>> skindata.bone_list.update_size()
        >>> [child.name for child in skelroot.children]
        ['bone1', 'geom']
        >>> skindata.set_transform(id44)
        >>> for bonedata in skindata.bone_list:
        ...     bonedata.set_transform(id44)
        >>> affectedbones = geom.flatten_skin()
        >>> [bone.name for bone in affectedbones]
        ['bone1', 'bone2', 'bone22', 'bone211']
        >>> [child.name for child in skelroot.children]
        ['geom', 'bone1', 'bone21', 'bone2', 'bone22', 'bone211']
        """
        def is_skin(self):
            """Returns True if geometry is skinned."""
            return self.skin_instance != None

        def _validate_skin(self):
            """Check that skinning blocks are valid. Will raise NifError exception
            if not."""
            if self.skin_instance == None: return
            if self.skin_instance.data == None:
                raise NifFormat.NifError('NiGeometry has NiSkinInstance without NiSkinData')
            if self.skin_instance.skeleton_root == None:
                raise NifFormat.NifError('NiGeometry has NiSkinInstance without skeleton root')
            if self.skin_instance.num_bones != self.skin_instance.data.num_bones:
                raise NifFormat.NifError('NiSkinInstance and NiSkinData have different number of bones')

        def add_bone(self, bone, vert_weights):
            """Add bone with given vertex weights.
            After adding all bones, the geometry skinning information should be set
            from the current position of the bones using the L{update_bind_position} function.

            :param bone: The bone NiNode block.
            :param vert_weights: A dictionary mapping each influenced vertex index to a vertex weight."""
            self._validate_skin()
            skininst = self.skin_instance
            skindata = skininst.data
            skelroot = skininst.skeleton_root

            bone_index = skininst.num_bones
            skininst.num_bones = bone_index+1
            skininst.bones.update_size()
            skininst.bones[bone_index] = bone
            skindata.num_bones = bone_index+1
            skindata.bone_list.update_size()
            skinbonedata = skindata.bone_list[bone_index]
            # set vertex weights
            skinbonedata.num_vertices = len(vert_weights)
            skinbonedata.vertex_weights.update_size()
            for i, (vert_index, vert_weight) in enumerate(vert_weights.iteritems()):
                skinbonedata.vertex_weights[i].index = vert_index
                skinbonedata.vertex_weights[i].weight = vert_weight



        def get_vertex_weights(self):
            """Get vertex weights in a convenient format: list bone and weight per
            vertex."""
            # shortcuts relevant blocks
            if not self.skin_instance:
                raise NifFormat.NifError('Cannot get vertex weights of geometry without skin.')
            self._validate_skin()
            geomdata = self.data
            skininst = self.skin_instance
            skindata = skininst.data
            # XXX todo: should we use list of dictionaries for this
            #           where each dict maps bone number to the weight?
            weights = [[] for i in xrange(geomdata.num_vertices)]
            for bonenum, bonedata in enumerate(skindata.bone_list):
                for skinweight in bonedata.vertex_weights:
                    # skip zero weights
                    if skinweight.weight != 0:
                        # boneweightlist is the list of (bonenum, weight) pairs that
                        # we must update now
                        boneweightlist = weights[skinweight.index]
                        # is bonenum already in there?
                        for i, (otherbonenum, otherweight) in enumerate(boneweightlist):
                            if otherbonenum == bonenum:
                                # yes! add the weight to the bone
                                boneweightlist[i][1] += skinweight.weight
                                break
                        else:
                            # nope... so add new [bone, weight] entry
                            boneweightlist.append([bonenum, skinweight.weight])
            return weights


        def flatten_skin(self):
            """Reposition all bone blocks and geometry block in the tree to be direct
            children of the skeleton root.

            Returns list of all used bones by the skin."""

            if not self.is_skin(): return [] # nothing to do

            result = [] # list of repositioned bones
            self._validate_skin() # validate the skin
            skininst = self.skin_instance
            skindata = skininst.data
            skelroot = skininst.skeleton_root

            # reparent geometry
            self.set_transform(self.get_transform(skelroot))
            geometry_parent = skelroot.find_chain(self, block_type = NifFormat.NiAVObject)[-2]
            geometry_parent.remove_child(self) # detatch geometry from tree
            skelroot.add_child(self, front = True) # and attatch it to the skeleton root

            # reparent all the bone blocks
            for bone_block in skininst.bones:
                # skeleton root, if it is used as bone, does not need to be processed
                if bone_block == skelroot: continue
                # get bone parent
                bone_parent = skelroot.find_chain(bone_block, block_type = NifFormat.NiAVObject)[-2]
                # set new child transforms
                for child in bone_block.children:
                    child.set_transform(child.get_transform(bone_parent))
                # reparent children
                for child in bone_block.children:
                    bone_parent.add_child(child)
                bone_block.num_children = 0
                bone_block.children.update_size() # = remove_child on each child
                # set new bone transform
                bone_block.set_transform(bone_block.get_transform(skelroot))
                # reparent bone block
                bone_parent.remove_child(bone_block)
                skelroot.add_child(bone_block)
                result.append(bone_block)

            return result



        # The nif skinning algorithm works as follows (as of nifskope):
        # v'                               # vertex after skinning in geometry space
        # = sum over {b in skininst.bones} # sum over all bones b that influence the mesh
        # weight[v][b]                     # how much bone b influences vertex v
        # * v                              # vertex before skinning in geometry space (as it is stored in the shape data)
        # * skindata.bone_list[b].transform # transform vertex to bone b space in the rest pose
        # * b.get_transform(skelroot)       # apply animation, by multiplying with all bone matrices in the chain down to the skeleton root; the vertex is now in skeleton root space
        # * skindata.transform             # transforms vertex from skeleton root space back to geometry space
        def get_skin_deformation(self):
            """Returns a list of vertices and normals in their final position after
            skinning, in geometry space."""

            if not self.data: return [], []

            if not self.is_skin(): return self.data.vertices, self.data.normals

            self._validate_skin()
            skininst = self.skin_instance
            skindata = skininst.data
            skelroot = skininst.skeleton_root

            vertices = [ NifFormat.Vector3() for i in xrange(self.data.num_vertices) ]
            normals = [ NifFormat.Vector3() for i in xrange(self.data.num_vertices) ]
            sumweights = [ 0.0 for i in xrange(self.data.num_vertices) ]
            skin_offset = skindata.get_transform()
            for i, bone_block in enumerate(skininst.bones):
                bonedata = skindata.bone_list[i]
                bone_offset = bonedata.get_transform()
                bone_matrix = bone_block.get_transform(skelroot)
                transform = bone_offset * bone_matrix * skin_offset
                scale, rotation, translation = transform.get_scale_rotation_translation()
                for skinweight in bonedata.vertex_weights:
                    index = skinweight.index
                    weight = skinweight.weight
                    vertices[index] += weight * (self.data.vertices[index] * transform)
                    if self.data.has_normals:
                        normals[index] += weight * (self.data.normals[index] * rotation)
                    sumweights[index] += weight

            for i, s in enumerate(sumweights):
                if abs(s - 1.0) > 0.01: 
                    logging.getLogger("pyffi.nif.nigeometry").warn(
                        "vertex %i has weights not summing to one" % i)

            return vertices, normals



        # ported and extended from niflib::NiNode::GoToSkeletonBindPosition() (r2518)
        def send_bones_to_bind_position(self):
            """Send all bones to their bind position.

            @deprecated: Use L{NifFormat.NiNode.send_bones_to_bind_position} instead of
                this function.
            """

            warnings.warn("use NifFormat.NiNode.send_bones_to_bind_position",
                          DeprecationWarning)

            if not self.is_skin():
                return

            # validate skin and set up quick links
            self._validate_skin()
            skininst = self.skin_instance
            skindata = skininst.data
            skelroot = skininst.skeleton_root

            # reposition the bones
            for i, parent_bone in enumerate(skininst.bones):
                parent_offset = skindata.bone_list[i].get_transform()
                # if parent_bone is a child of the skeleton root, then fix its
                # transfrom
                if parent_bone in skelroot.children:
                    parent_bone.set_transform(parent_offset.get_inverse() * self.get_transform(skelroot))
                # fix the transform of all its children
                for j, child_bone in enumerate(skininst.bones):
                    if child_bone not in parent_bone.children: continue
                    child_offset = skindata.bone_list[j].get_transform()
                    child_matrix = child_offset.get_inverse() * parent_offset
                    child_bone.set_transform(child_matrix)



        # ported from niflib::NiSkinData::ResetOffsets (r2561)
        def update_bind_position(self):
            """Make current position of the bones the bind position for this geometry.

            Sets the NiSkinData overall transform to the inverse of the geometry transform
            relative to the skeleton root, and sets the NiSkinData of each bone to
            the geometry transform relative to the skeleton root times the inverse of the bone
            transform relative to the skeleton root."""
            if not self.is_skin(): return

            # validate skin and set up quick links
            self._validate_skin()
            skininst = self.skin_instance
            skindata = skininst.data
            skelroot = skininst.skeleton_root

            # calculate overall offset
            geomtransform = self.get_transform(skelroot)
            skindata.set_transform(geomtransform.get_inverse())

            # calculate bone offsets
            for i, bone in enumerate(skininst.bones):
                 skindata.bone_list[i].set_transform(geomtransform * bone.get_transform(skelroot).get_inverse())

        def get_skin_partition(self):
            """Return the skin partition block."""
            skininst = self.skin_instance
            if not skininst:
                skinpart = None
            else:
                skinpart = skininst.skin_partition
                if not skinpart:
                    skindata = skininst.data
                    if skindata:
                        skinpart = skindata.skin_partition

            return skinpart

        def set_skin_partition(self, skinpart):
            """Set skin partition block."""
            skininst = self.skin_instance
            if not skininst:
                raise ValueError("Geometry has no skin instance.")

            skindata = skininst.data
            if not skindata:
                raise ValueError("Geometry has no skin data.")

            skininst.skin_partition = skinpart
            skindata.skin_partition = skinpart

    class NiKeyframeData:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            for key in self.translations.keys:
                key.value.x *= scale
                key.value.y *= scale
                key.value.z *= scale
                #key.forward.x *= scale
                #key.forward.y *= scale
                #key.forward.z *= scale
                #key.backward.x *= scale
                #key.backward.y *= scale
                #key.backward.z *= scale
                # what to do with TBC?

    class NiMaterialColorController:
        def get_target_color(self):
            """Get target color (works for all nif versions)."""
            return ((self.flags >> 4) & 7) | self.target_color

        def set_target_color(self, target_color):
            """Set target color (works for all nif versions)."""
            self.flags |= (target_color & 7) << 4
            self.target_color = target_color

    class NiMorphData:
        def apply_scale(self, scale):
            """Apply scale factor on data."""
            for morph in self.morphs:
                for v in morph.vectors:
                    v.x *= scale
                    v.y *= scale
                    v.z *= scale

    class NiNode:
        """
        >>> from pyffi.formats.nif import NifFormat
        >>> x = NifFormat.NiNode()
        >>> y = NifFormat.NiNode()
        >>> z = NifFormat.NiNode()
        >>> x.num_children =1
        >>> x.children.update_size()
        >>> y in x.children
        False
        >>> x.children[0] = y
        >>> y in x.children
        True
        >>> x.add_child(z, front = True)
        >>> x.add_child(y)
        >>> x.num_children
        2
        >>> x.children[0] is z
        True
        >>> x.remove_child(y)
        >>> y in x.children
        False
        >>> x.num_children
        1
        >>> e = NifFormat.NiSpotLight()
        >>> x.add_effect(e)
        >>> x.num_effects
        1
        >>> e in x.effects
        True

        >>> from pyffi.formats.nif import NifFormat
        >>> node = NifFormat.NiNode()
        >>> child1 = NifFormat.NiNode()
        >>> child1.name = "hello"
        >>> child_2 = NifFormat.NiNode()
        >>> child_2.name = "world"
        >>> node.get_children()
        []
        >>> node.set_children([child1, child_2])
        >>> [child.name for child in node.get_children()]
        ['hello', 'world']
        >>> [child.name for child in node.children]
        ['hello', 'world']
        >>> node.set_children([])
        >>> node.get_children()
        []
        >>> # now set them the other way around
        >>> node.set_children([child_2, child1])
        >>> [child.name for child in node.get_children()]
        ['world', 'hello']
        >>> [child.name for child in node.children]
        ['world', 'hello']
        >>> node.remove_child(child_2)
        >>> [child.name for child in node.children]
        ['hello']
        >>> node.add_child(child_2)
        >>> [child.name for child in node.children]
        ['hello', 'world']

        >>> from pyffi.formats.nif import NifFormat
        >>> node = NifFormat.NiNode()
        >>> effect1 = NifFormat.NiSpotLight()
        >>> effect1.name = "hello"
        >>> effect2 = NifFormat.NiSpotLight()
        >>> effect2.name = "world"
        >>> node.get_effects()
        []
        >>> node.set_effects([effect1, effect2])
        >>> [effect.name for effect in node.get_effects()]
        ['hello', 'world']
        >>> [effect.name for effect in node.effects]
        ['hello', 'world']
        >>> node.set_effects([])
        >>> node.get_effects()
        []
        >>> # now set them the other way around
        >>> node.set_effects([effect2, effect1])
        >>> [effect.name for effect in node.get_effects()]
        ['world', 'hello']
        >>> [effect.name for effect in node.effects]
        ['world', 'hello']
        >>> node.remove_effect(effect2)
        >>> [effect.name for effect in node.effects]
        ['hello']
        >>> node.add_effect(effect2)
        >>> [effect.name for effect in node.effects]
        ['hello', 'world']
        """
        def add_child(self, child, front=False):
            """Add block to child list.

            :param child: The child to add.
            :type child: L{NifFormat.NiAVObject}
            :keyword front: Whether to add to the front or to the end of the
                list (default is at end).
            :type front: ``bool``
            """
            # check if it's already a child
            if child in self.children:
                return
            # increase number of children
            num_children = self.num_children
            self.num_children = num_children + 1
            self.children.update_size()
            # add the child
            if not front:
                self.children[num_children] = child
            else:
                for i in xrange(num_children, 0, -1):
                    self.children[i] = self.children[i-1]
                self.children[0] = child

        def remove_child(self, child):
            """Remove a block from the child list.

            :param child: The child to remove.
            :type child: L{NifFormat.NiAVObject}
            """
            self.set_children([otherchild for otherchild in self.get_children()
                              if not(otherchild is child)])

        def get_children(self):
            """Return a list of the children of the block.

            :return: The list of children.
            :rtype: ``list`` of L{NifFormat.NiAVObject}
            """
            return [child for child in self.children]

        def set_children(self, childlist):
            """Set the list of children from the given list (destroys existing list).

            :param childlist: The list of child blocks to set.
            :type childlist: ``list`` of L{NifFormat.NiAVObject}
            """
            self.num_children = len(childlist)
            self.children.update_size()
            for i, child in enumerate(childlist):
                self.children[i] = child

        def add_effect(self, effect):
            """Add an effect to the list of effects.

            :param effect: The effect to add.
            :type effect: L{NifFormat.NiDynamicEffect}
            """
            num_effs = self.num_effects
            self.num_effects = num_effs + 1
            self.effects.update_size()
            self.effects[num_effs] = effect

        def remove_effect(self, effect):
            """Remove a block from the effect list.

            :param effect: The effect to remove.
            :type effect: L{NifFormat.NiDynamicEffect}
            """
            self.set_effects([othereffect for othereffect in self.get_effects()
                             if not(othereffect is effect)])

        def get_effects(self):
            """Return a list of the effects of the block.

            :return: The list of effects.
            :rtype: ``list`` of L{NifFormat.NiDynamicEffect}
            """
            return [effect for effect in self.effects]

        def set_effects(self, effectlist):
            """Set the list of effects from the given list (destroys existing list).

            :param effectlist: The list of effect blocks to set.
            :type effectlist: ``list`` of L{NifFormat.NiDynamicEffect}
            """
            self.num_effects = len(effectlist)
            self.effects.update_size()
            for i, effect in enumerate(effectlist):
                self.effects[i] = effect

        def merge_external_skeleton_root(self, skelroot):
            """Attach skinned geometry to self (which will be the new skeleton root of
            the nif at the given skeleton root). Use this function if you move a
            skinned geometry from one nif into a new nif file. The bone links will be
            updated to point to the tree at self, instead of to the external tree.
            """
            # sanity check
            if self.name != skelroot.name:
                raise ValueError("skeleton root names do not match")

            # get a dictionary mapping bone names to bone blocks
            bone_dict = {}
            for block in self.tree():
                if isinstance(block, NifFormat.NiNode):
                    if block.name:
                        if block.name in bone_dict:
                            raise ValueError(
                                "multiple NiNodes with name %s" % block.name)
                        bone_dict[block.name] = block

            # add all non-bone children of the skeleton root to self
            for child in skelroot.get_children():
                # skip empty children
                if not child:
                    continue
                # skip bones
                if child.name in bone_dict:
                    continue
                # not a bone, so add it
                self.add_child(child)
                # fix links to skeleton root and bones
                for externalblock in child.tree():
                    if isinstance(externalblock, NifFormat.NiSkinInstance):
                        if not(externalblock.skeleton_root is skelroot):
                            raise ValueError(
                                "expected skeleton root %s but got %s"
                                % (skelroot.name, externalblock.skeleton_root.name))
                        externalblock.skeleton_root = self
                        for i, externalbone in enumerate(externalblock.bones):
                            externalblock.bones[i] = bone_dict[externalbone.name]

        def merge_skeleton_roots(self):
            """This function will look for other geometries whose skeleton
            root is a (possibly indirect) child of this node. It will then
            reparent those geometries to this node. For example, it will unify
            the skeleton roots in Morrowind's cliffracer.nif file, or of the
            (official) body skins. This makes it much easier to import
            skeletons in for instance Blender: there will be only one skeleton
            root for each bone, over all geometries.

            The merge fails for those geometries whose global skin data
            transform does not match the inverse geometry transform relative to
            the skeleton root (the maths does not work out in this case!)

            Returns list of all new blocks that have been reparented (and
            added to the skeleton root children list), and a list of blocks
            for which the merge failed.
            """
            logger = logging.getLogger("pyffi.nif.ninode")

            result = [] # list of reparented blocks
            failed = [] # list of blocks that could not be reparented

            id44 = NifFormat.Matrix44()
            id44.set_identity()

            # find the root block (direct parent of skeleton root that connects to the geometry) for each of these geometries
            for geom in self.get_global_iterator():
                # make sure we only do each geometry once
                if (geom in result) or (geom in failed):
                    continue
                # only geometries
                if not isinstance(geom, NifFormat.NiGeometry):
                    continue
                # only skins
                if not geom.is_skin():
                    continue
                # only if they have a different skeleton root
                if geom.skin_instance.skeleton_root is self:
                    continue
                # check transforms
                if (geom.skin_instance.data.get_transform()
                    * geom.get_transform(geom.skin_instance.skeleton_root) != id44):
                    logger.warn(
                        "can't rebase %s: global skin data transform does not match "
                        "geometry transform relative to skeleton root" % geom.name)
                    failed.append(geom)
                    continue # skip this one
                # everything ok!
                # find geometry parent
                geomroot = geom.skin_instance.skeleton_root.find_chain(geom)[-2]
                # reparent
                logger.debug("detaching %s from %s" % (geom.name, geomroot.name))
                geomroot.remove_child(geom)
                logger.debug("attaching %s to %s" % (geom.name, self.name))
                self.add_child(geom)
                # set its new skeleton root
                geom.skin_instance.skeleton_root = self
                # fix transform
                geom.skin_instance.data.set_transform(
                    geom.get_transform(self).get_inverse(fast=False))
                # and signal that we reparented this block
                result.append(geom)

            return result, failed

        def get_skinned_geometries(self):
            """This function yields all skinned geometries which have self as
            skeleton root.
            """
            for geom in self.get_global_iterator():
                if (isinstance(geom, NifFormat.NiGeometry)
                    and geom.is_skin()
                    and geom.skin_instance.skeleton_root is self):
                    yield geom

        def send_geometries_to_bind_position(self):
            """Call this on the skeleton root of geometries. This function will
            transform the geometries, such that all skin data transforms coincide, or
            at least coincide partially.

            :return: A number quantifying the remaining difference between bind
                positions.
            :rtype: ``float``
            """
            # get logger
            logger = logging.getLogger("pyffi.nif.ninode")
            # maps bone name to bind position transform matrix (relative to
            # skeleton root)
            bone_bind_transform = {}
            # find all skinned geometries with self as skeleton root
            geoms = list(self.get_skinned_geometries())
            # sort geometries by bone level
            # this ensures that "parent" geometries serve as reference for "child"
            # geometries
            sorted_geoms = []
            for bone in self.get_global_iterator():
                if not isinstance(bone, NifFormat.NiNode):
                    continue
                for geom in geoms:
                    if not geom in sorted_geoms:
                        if bone in geom.skin_instance.bones:
                            sorted_geoms.append(geom)
            geoms = sorted_geoms
            # now go over all geometries and synchronize their relative bind poses
            for geom in geoms:
                skininst = geom.skin_instance
                skindata = skininst.data
                # set difference matrix to identity
                diff = NifFormat.Matrix44()
                diff.set_identity()
                # go over all bones in current geometry, see if it has been visited
                # before
                for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                    # bonenode can be None; see pyffi issue #3114079
                    if not bonenode:
                        continue
                    if bonenode.name in bone_bind_transform:
                        # calculate difference
                        # (see explanation below)
                        diff = (bonedata.get_transform()
                                * bone_bind_transform[bonenode.name]
                                * geom.get_transform(self).get_inverse(fast=False))
                        break

                if diff.is_identity():
                    logger.debug("%s is already in bind position" % geom.name)
                else:
                    logger.info("fixing %s bind position" % geom.name)
                    # explanation:
                    # we must set the bonedata transform T' such that its bone bind
                    # position matrix
                    #   T'^-1 * G
                    # (where T' = the updated bonedata.get_transform()
                    # and G = geom.get_transform(self))
                    # coincides with the desired matrix
                    #   B = bone_bind_transform[bonenode.name]
                    # in other words:
                    #   T' = G * B^-1
                    # or, with diff = D = T * B * G^-1
                    #   T' = D^-1 * T
                    # to keep the geometry in sync, the vertices and normals must
                    # be multiplied with D, e.g. v' = v * D
                    # because the full transform
                    #    v * T * ... = v * D * D^-1 * T * ... = v' * T' * ...
                    # must be kept invariant
                    for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                        # bonenode can be None; see pyffi issue #3114079
                        logger.debug(
                            "transforming bind position of bone %s"
                            % bonenode.name if bonenode else "<None>")
                        bonedata.set_transform(diff.get_inverse(fast=False)
                                               * bonedata.get_transform())
                    # transform geometry
                    logger.debug("transforming vertices and normals")
                    for vert in geom.data.vertices:
                        newvert = vert * diff
                        vert.x = newvert.x
                        vert.y = newvert.y
                        vert.z = newvert.z
                    for norm in geom.data.normals:
                        newnorm = norm * diff.get_matrix_33()
                        norm.x = newnorm.x
                        norm.y = newnorm.y
                        norm.z = newnorm.z

                # store updated bind position for future reference
                for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                    # bonenode can be None; see pyffi issue #3114079
                    if not bonenode:
                        continue
                    bone_bind_transform[bonenode.name] = (
                        bonedata.get_transform().get_inverse(fast=False)
                        * geom.get_transform(self))

            # validation: check that bones share bind position
            bone_bind_transform = {}
            error = 0.0
            for geom in geoms:
                skininst = geom.skin_instance
                skindata = skininst.data
                # go over all bones in current geometry, see if it has been visited
                # before
                for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                    if not bonenode:
                        # bonenode can be None; see pyffi issue #3114079
                        continue
                    if bonenode.name in bone_bind_transform:
                        # calculate difference
                        diff = ((bonedata.get_transform().get_inverse(fast=False)
                                 * geom.get_transform(self))
                                - bone_bind_transform[bonenode.name])
                        # calculate error (sup norm)
                        error = max(error,
                                    max(max(abs(elem) for elem in row)
                                        for row in diff.as_list()))
                    else:
                        bone_bind_transform[bonenode.name] = (
                            bonedata.get_transform().get_inverse(fast=False)
                            * geom.get_transform(self))

            logger.debug("Geometry bind position error is %f" % error)
            if error > 1e-3:
                logger.warning("Failed to send some geometries to bind position")
            return error

        def send_detached_geometries_to_node_position(self):
            """Some nifs (in particular in Morrowind) have geometries that are skinned
            but that do not share bones. In such cases, send_geometries_to_bind_position
            cannot reposition them. This function will send such geometries to the
            position of their root node.

            Examples of such nifs are the official Morrowind skins (after merging
            skeleton roots).

            Returns list of detached geometries that have been moved.
            """
            logger = logging.getLogger("pyffi.nif.ninode")
            geoms = list(self.get_skinned_geometries())

            # parts the geometries into sets that do not share bone influences
            # * first construct sets of bones, merge intersecting sets
            # * then check which geometries belong to which set
            # (note: bone can be None, see issue #3114079)
            bonesets = [
                list(set(bone for bone in geom.skin_instance.bones if bone))
                for geom in geoms]
            # the merged flag signals that we are still merging bones
            merged = True
            while merged:
                merged = False
                for boneset in bonesets:
                    for other_boneset in bonesets:
                        # skip if sets are identical
                        if other_boneset is boneset:
                            continue
                        # if not identical, see if they can be merged
                        if set(other_boneset) & set(boneset):
                            # XXX hackish but works
                            # calculate union
                            updated_boneset = list(set(other_boneset) | set(boneset))
                            # and move all bones into one bone set
                            del other_boneset[:]
                            del boneset[:]
                            boneset += updated_boneset
                            merged = True
            # remove empty bone sets
            bonesets = list(boneset for boneset in bonesets if boneset)
            logger.debug("bones per partition are")
            for boneset in bonesets:
                logger.debug(str([bone.name for bone in boneset]))
            parts = [[geom for geom in geoms
                          if set(geom.skin_instance.bones) & set(boneset)]
                         for boneset in bonesets]
            logger.debug("geometries per partition are")
            for part in parts:
                logger.debug(str([geom.name for geom in part]))
            # if there is only one set, we are done
            if len(bonesets) <= 1:
                logger.debug("no detached geometries")
                return []

            # next, for each part, move all geometries so the lowest bone matches the
            # node transform
            for boneset, part in izip(bonesets, parts):
                logger.debug("moving part %s" % str([geom.name for geom in part]))
                # find "lowest" bone in the bone set
                lowest_dist = None
                lowest_bonenode = None
                for bonenode in boneset:
                    dist = len(self.find_chain(bonenode))
                    if (lowest_dist is None) or (lowest_dist > dist):
                        lowest_dist = dist
                        lowest_bonenode = bonenode
                logger.debug("reference bone is %s" % lowest_bonenode.name)
                # find a geometry that has this bone
                for geom in part:
                    for bonenode, bonedata in izip(geom.skin_instance.bones,
                                                   geom.skin_instance.data.bone_list):
                        if bonenode is lowest_bonenode:
                            lowest_geom = geom
                            lowest_bonedata = bonedata
                            break
                    else:
                        continue
                    break
                else:
                    raise RuntimeError("no reference geometry with this bone: bug?")
                # calculate matrix
                diff = (lowest_bonedata.get_transform()
                        * lowest_bonenode.get_transform(self)
                        * lowest_geom.get_transform(self).get_inverse(fast=False))
                if diff.is_identity():
                    logger.debug("%s is already in node position"
                                 % lowest_bonenode.name)
                    continue
                # now go over all geometries and synchronize their position to the
                # reference bone
                for geom in part:
                    logger.info("moving %s to node position" % geom.name)
                    # XXX we're using this trick a few times now
                    # XXX move it to a separate NiGeometry function
                    skininst = geom.skin_instance
                    skindata = skininst.data
                    # explanation:
                    # we must set the bonedata transform T' such that its bone bind
                    # position matrix
                    #   T'^-1 * G
                    # (where T' = the updated lowest_bonedata.get_transform()
                    # and G = geom.get_transform(self))
                    # coincides with the desired matrix
                    #   B = lowest_bonenode.get_transform(self)
                    # in other words:
                    #   T' = G * B^-1
                    # or, with diff = D = T * B * G^-1
                    #   T' = D^-1 * T
                    # to keep the geometry in sync, the vertices and normals must
                    # be multiplied with D, e.g. v' = v * D
                    # because the full transform
                    #    v * T * ... = v * D * D^-1 * T * ... = v' * T' * ...
                    # must be kept invariant
                    for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                        logger.debug("transforming bind position of bone %s"
                                     % bonenode.name)
                        bonedata.set_transform(diff.get_inverse(fast=False)
                                              * bonedata.get_transform())
                    # transform geometry
                    logger.debug("transforming vertices and normals")
                    for vert in geom.data.vertices:
                        newvert = vert * diff
                        vert.x = newvert.x
                        vert.y = newvert.y
                        vert.z = newvert.z
                    for norm in geom.data.normals:
                        newnorm = norm * diff.get_matrix_33()
                        norm.x = newnorm.x
                        norm.y = newnorm.y
                        norm.z = newnorm.z

        def send_bones_to_bind_position(self):
            """This function will send all bones of geometries of this skeleton root
            to their bind position. For best results, call
            L{send_geometries_to_bind_position} first.

            :return: A number quantifying the remaining difference between bind
                positions.
            :rtype: ``float``
            """
            # get logger
            logger = logging.getLogger("pyffi.nif.ninode")
            # check all bones and bone datas to see if a bind position exists
            bonelist = []
            error = 0.0
            geoms = list(self.get_skinned_geometries())
            for geom in geoms:
                skininst = geom.skin_instance
                skindata = skininst.data
                for bonenode, bonedata in izip(skininst.bones, skindata.bone_list):
                    # bonenode can be None; see pyffi issue #3114079
                    if not bonenode:
                        continue
                    # make sure all bone data of shared bones coincides
                    for othergeom, otherbonenode, otherbonedata in bonelist:
                        if bonenode is otherbonenode:
                            diff = ((otherbonedata.get_transform().get_inverse(fast=False)
                                     *
                                     othergeom.get_transform(self))
                                    -
                                    (bonedata.get_transform().get_inverse(fast=False)
                                     *
                                     geom.get_transform(self)))
                            if diff.sup_norm() > 1e-3:
                                logger.warning("Geometries %s and %s do not share the same bind position: bone %s will be sent to a position matching only one of these" % (geom.name, othergeom.name, bonenode.name))
                            # break the loop
                            break
                    else:
                        # the loop did not break, so the bone was not yet added
                        # add it now
                        logger.debug("Found bind position data for %s" % bonenode.name)
                        bonelist.append((geom, bonenode, bonedata))

            # the algorithm simply makes all transforms correct by changing
            # each local bone matrix in such a way that the global matrix
            # relative to the skeleton root matches the skinning information

            # this algorithm is numerically most stable if bones are traversed
            # in hierarchical order, so first sort the bones
            sorted_bonelist = []
            for node in self.tree():
                if not isinstance(node, NifFormat.NiNode):
                    continue
                for geom, bonenode, bonedata in bonelist:
                    if node is bonenode:
                        sorted_bonelist.append((geom, bonenode, bonedata))
            bonelist = sorted_bonelist
            # now reposition the bones
            for geom, bonenode, bonedata in bonelist:
                # explanation:
                # v * CHILD * PARENT * ...
                # = v * CHILD * DIFF^-1 * DIFF * PARENT * ...
                # and now choose DIFF such that DIFF * PARENT * ... = desired transform

                # calculate desired transform relative to skeleton root
                # transform is DIFF * PARENT
                transform = (bonedata.get_transform().get_inverse(fast=False)
                             * geom.get_transform(self))
                # calculate difference
                diff = transform * bonenode.get_transform(self).get_inverse(fast=False)
                if not diff.is_identity():
                    logger.info("Sending %s to bind position"
                                % bonenode.name)
                    # fix transform of this node
                    bonenode.set_transform(diff * bonenode.get_transform())
                    # fix transform of all its children
                    diff_inv = diff.get_inverse(fast=False)
                    for childnode in bonenode.children:
                        if childnode:
                            childnode.set_transform(childnode.get_transform() * diff_inv)
                else:
                    logger.debug("%s is already in bind position"
                                 % bonenode.name)

            # validate
            error = 0.0
            diff_error = 0.0
            for geom in geoms:
                skininst = geom.skin_instance
                skindata = skininst.data
                # calculate geometry transform
                geomtransform = geom.get_transform(self)
                # check skin data fields (also see NiGeometry.update_bind_position)
                for i, bone in enumerate(skininst.bones):
                    # bone can be None; see pyffi issue #3114079
                    if bone is None:
                        continue
                    diff = ((skindata.bone_list[i].get_transform().get_inverse(fast=False)
                             * geomtransform)
                            - bone.get_transform(self))
                    # calculate error (sup norm)
                    diff_error = max(max(abs(elem) for elem in row)
                                     for row in diff.as_list())
                    if diff_error > 1e-3:
                        logger.warning(
                            "Failed to set bind position of bone %s for geometry %s (error is %f)"
                            % (bone.name, geom.name, diff_error))
                    error = max(error, diff_error)

            logger.debug("Bone bind position maximal error is %f" % error)
            if error > 1e-3:
                logger.warning("Failed to send some bones to bind position")
            return error

    class NiObjectNET:
        def add_extra_data(self, extrablock):
            """Add block to extra data list and extra data chain. It is good practice
            to ensure that the extra data has empty next_extra_data field when adding it
            to avoid loops in the hierarchy."""
            # add to the list
            num_extra = self.num_extra_data_list
            self.num_extra_data_list = num_extra + 1
            self.extra_data_list.update_size()
            self.extra_data_list[num_extra] = extrablock
            # add to the chain
            if not self.extra_data:
                self.extra_data = extrablock
            else:
                lastextra = self.extra_data
                while lastextra.next_extra_data:
                    lastextra = lastextra.next_extra_data
                lastextra.next_extra_data = extrablock

        def remove_extra_data(self, extrablock):
            """Remove block from extra data list and extra data chain.

            >>> from pyffi.formats.nif import NifFormat
            >>> block = NifFormat.NiNode()
            >>> block.num_extra_data_list = 3
            >>> block.extra_data_list.update_size()
            >>> extrablock = NifFormat.NiStringExtraData()
            >>> block.extra_data_list[1] = extrablock
            >>> block.remove_extra_data(extrablock)
            >>> [extra for extra in block.extra_data_list]
            [None, None]
            """
            # remove from list
            new_extra_list = []
            for extraother in self.extra_data_list:
                if not extraother is extrablock:
                    new_extra_list.append(extraother)
            self.num_extra_data_list = len(new_extra_list)
            self.extra_data_list.update_size()
            for i, extraother in enumerate(new_extra_list):
                self.extra_data_list[i] = extraother
            # remove from chain
            if self.extra_data is extrablock:
                self.extra_data = extrablock.next_extra_data
            lastextra = self.extra_data
            while lastextra:
                if lastextra.next_extra_data is extrablock:
                    lastextra.next_extra_data = lastextra.next_extra_data.next_extra_data
                lastextra = lastextra.next_extra_data

        def get_extra_datas(self):
            """Get a list of all extra data blocks."""
            xtras = [xtra for xtra in self.extra_data_list]
            xtra = self.extra_data
            while xtra:
                if not xtra in self.extra_data_list:
                    xtras.append(xtra)
                xtra = xtra.next_extra_data
            return xtras

        def set_extra_datas(self, extralist):
            """Set all extra data blocks from given list (erases existing data).

            >>> from pyffi.formats.nif import NifFormat
            >>> node = NifFormat.NiNode()
            >>> extra1 = NifFormat.NiExtraData()
            >>> extra1.name = "hello"
            >>> extra2 = NifFormat.NiExtraData()
            >>> extra2.name = "world"
            >>> node.get_extra_datas()
            []
            >>> node.set_extra_datas([extra1, extra2])
            >>> [extra.name for extra in node.get_extra_datas()]
            ['hello', 'world']
            >>> [extra.name for extra in node.extra_data_list]
            ['hello', 'world']
            >>> node.extra_data is extra1
            True
            >>> extra1.next_extra_data is extra2
            True
            >>> extra2.next_extra_data is None
            True
            >>> node.set_extra_datas([])
            >>> node.get_extra_datas()
            []
            >>> # now set them the other way around
            >>> node.set_extra_datas([extra2, extra1])
            >>> [extra.name for extra in node.get_extra_datas()]
            ['world', 'hello']
            >>> [extra.name for extra in node.extra_data_list]
            ['world', 'hello']
            >>> node.extra_data is extra2
            True
            >>> extra2.next_extra_data is extra1
            True
            >>> extra1.next_extra_data is None
            True

            :param extralist: List of extra data blocks to add.
            :type extralist: ``list`` of L{NifFormat.NiExtraData}
            """
            # set up extra data list
            self.num_extra_data_list = len(extralist)
            self.extra_data_list.update_size()
            for i, extra in enumerate(extralist):
                self.extra_data_list[i] = extra
            # set up extra data chain
            # first, kill the current chain
            self.extra_data = None
            # now reconstruct it
            if extralist:
                self.extra_data = extralist[0]
                lastextra = self.extra_data
                for extra in extralist[1:]:
                    lastextra.next_extra_data = extra
                    lastextra = extra
                lastextra.next_extra_data = None

        def add_controller(self, ctrlblock):
            """Add block to controller chain and set target of controller to self."""
            if not self.controller:
                self.controller = ctrlblock
            else:
                lastctrl = self.controller
                while lastctrl.next_controller:
                    lastctrl = lastctrl.next_controller
                lastctrl.next_controller = ctrlblock
            # set the target of the controller
            ctrlblock.target = self

        def get_controllers(self):
            """Get a list of all controllers."""
            ctrls = []
            ctrl = self.controller
            while ctrl:
                ctrls.append(ctrl)
                ctrl = ctrl.next_controller
            return ctrls

        def add_integer_extra_data(self, name, value):
            """Add a particular extra integer data block."""
            extra = NifFormat.NiIntegerExtraData()
            extra.name = name
            extra.integer_data = value
            self.add_extra_data(extra)

    class NiObject:
        def find(self, block_name = None, block_type = None):
            # does this block match the search criteria?
            if block_name and block_type:
                if isinstance(self, block_type):
                    try:
                        if block_name == self.name: return self
                    except AttributeError:
                        pass
            elif block_name:
                try:
                    if block_name == self.name: return self
                except AttributeError:
                    pass
            elif block_type:
                if isinstance(self, block_type): return self

            # ok, this block is not a match, so check further down in tree
            for child in self.get_refs():
                blk = child.find(block_name, block_type)
                if blk: return blk

            return None

        def find_chain(self, block, block_type = None):
            """Finds a chain of blocks going from C{self} to C{block}. If found,
            self is the first element and block is the last element. If no branch
            found, returns an empty list. Does not check whether there is more
            than one branch; if so, the first one found is returned.

            :param block: The block to find a chain to.
            :param block_type: The type that blocks should have in this chain."""

            if self is block: return [self]
            for child in self.get_refs():
                if block_type and not isinstance(child, block_type): continue
                child_chain = child.find_chain(block, block_type)
                if child_chain:
                    return [self] + child_chain

            return []

        def apply_scale(self, scale):
            """Scale data in this block. This implementation does nothing.
            Override this method if it contains geometry data that can be
            scaled.
            """
            pass

        def tree(self, block_type = None, follow_all = True, unique = False):
            """A generator for parsing all blocks in the tree (starting from and
            including C{self}).

            :param block_type: If not ``None``, yield only blocks of the type C{block_type}.
            :param follow_all: If C{block_type} is not ``None``, then if this is ``True`` the function will parse the whole tree. Otherwise, the function will not follow branches that start by a non-C{block_type} block.

            :param unique: Whether the generator can return the same block twice or not."""
            # unique blocks: reduce this to the case of non-unique blocks
            if unique:
                block_list = []
                for block in self.tree(block_type = block_type, follow_all = follow_all, unique = False):
                    if not block in block_list:
                        yield block
                        block_list.append(block)
                return

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

        def _validateTree(self):
            """Raises ValueError if there is a cycle in the tree."""
            # If the tree is parsed, then each block should be visited once.
            # However, as soon as some cycle is present, parsing the tree
            # will visit some child more than once (and as a consequence, infinitely
            # many times). So, walk the reference tree and check that every block is
            # only visited once.
            children = []
            for child in self.tree():
                if child in children:
                    raise ValueError('cyclic references detected')
                children.append(child)

        def is_interchangeable(self, other):
            """Are the two blocks interchangeable?

            @todo: Rely on AnyType, SimpleType, ComplexType, etc. implementation.
            """
            if isinstance(self, (NifFormat.NiProperty, NifFormat.NiSourceTexture)):
                # use hash for properties and source textures
                return ((self.__class__ is other.__class__)
                        and (self.get_hash() == other.get_hash()))
            else:
                # for blocks with references: quick check only
                return self is other

    class NiMaterialProperty:
        def is_interchangeable(self, other):
            """Are the two material blocks interchangeable?"""
            specialnames = ("envmap2", "envmap", "skin", "hair",
                            "dynalpha", "hidesecret", "lava")
            if self.__class__ is not other.__class__:
                return False
            if (self.name.lower() in specialnames
                or other.name.lower() in specialnames):
                # do not ignore name
                return self.get_hash() == other.get_hash()
            else:
                # ignore name
                return self.get_hash()[1:] == other.get_hash()[1:]

    class ATextureRenderData:
        def save_as_dds(self, stream):
            """Save image as DDS file."""
            # set up header and pixel data
            data = pyffi.formats.dds.DdsFormat.Data()
            header = data.header
            pixeldata = data.pixeldata

            # create header, depending on the format
            if self.pixel_format in (NifFormat.PixelFormat.PX_FMT_RGB8,
                                     NifFormat.PixelFormat.PX_FMT_RGBA8):
                # uncompressed RGB(A)
                header.flags.caps = 1
                header.flags.height = 1
                header.flags.width = 1
                header.flags.pixel_format = 1
                header.flags.mipmap_count = 1
                header.flags.linear_size = 1
                header.height = self.mipmaps[0].height
                header.width = self.mipmaps[0].width
                header.linear_size = len(self.pixel_data)
                header.mipmap_count = len(self.mipmaps)
                header.pixel_format.flags.rgb = 1
                header.pixel_format.bit_count = self.bits_per_pixel
                if not self.channels:
                    header.pixel_format.r_mask = self.red_mask
                    header.pixel_format.g_mask = self.green_mask
                    header.pixel_format.b_mask = self.blue_mask
                    header.pixel_format.a_mask = self.alpha_mask
                else:
                    bit_pos = 0
                    for i, channel in enumerate(self.channels):
                        mask = (2 ** channel.bits_per_channel - 1) << bit_pos
                        if channel.type == NifFormat.ChannelType.CHNL_RED:
                            header.pixel_format.r_mask = mask
                        elif channel.type == NifFormat.ChannelType.CHNL_GREEN:
                            header.pixel_format.g_mask = mask
                        elif channel.type == NifFormat.ChannelType.CHNL_BLUE:
                            header.pixel_format.b_mask = mask
                        elif channel.type == NifFormat.ChannelType.CHNL_ALPHA:
                            header.pixel_format.a_mask = mask
                        bit_pos += channel.bits_per_channel
                header.caps_1.complex = 1
                header.caps_1.texture = 1
                header.caps_1.mipmap = 1
                if self.pixel_data:
                    # used in older nif versions
                    pixeldata.set_value(self.pixel_data)
                else:
                    # used in newer nif versions
                    pixeldata.set_value(''.join(self.pixel_data_matrix))
            elif self.pixel_format == NifFormat.PixelFormat.PX_FMT_DXT1:
                # format used in Megami Tensei: Imagine and Bully SE
                header.flags.caps = 1
                header.flags.height = 1
                header.flags.width = 1
                header.flags.pixel_format = 1
                header.flags.mipmap_count = 1
                header.flags.linear_size = 0
                header.height = self.mipmaps[0].height
                header.width = self.mipmaps[0].width
                header.linear_size = 0
                header.mipmap_count = len(self.mipmaps)
                header.pixel_format.flags.four_c_c = 1
                header.pixel_format.four_c_c = pyffi.formats.dds.DdsFormat.FourCC.DXT1
                header.pixel_format.bit_count = 0
                header.pixel_format.r_mask = 0
                header.pixel_format.g_mask = 0
                header.pixel_format.b_mask = 0
                header.pixel_format.a_mask = 0
                header.caps_1.complex = 1
                header.caps_1.texture = 1
                header.caps_1.mipmap = 1
                if isinstance(self,
                              NifFormat.NiPersistentSrcTextureRendererData):
                    pixeldata.set_value(
                        ''.join(
                            ''.join([chr(x) for x in tex])
                            for tex in self.pixel_data))
                else:
                    pixeldata.set_value(''.join(self.pixel_data_matrix))
            elif self.pixel_format in (NifFormat.PixelFormat.PX_FMT_DXT5,
                                       NifFormat.PixelFormat.PX_FMT_DXT5_ALT):
                # format used in Megami Tensei: Imagine
                header.flags.caps = 1
                header.flags.height = 1
                header.flags.width = 1
                header.flags.pixel_format = 1
                header.flags.mipmap_count = 1
                header.flags.linear_size = 0
                header.height = self.mipmaps[0].height
                header.width = self.mipmaps[0].width
                header.linear_size = 0
                header.mipmap_count = len(self.mipmaps)
                header.pixel_format.flags.four_c_c = 1
                header.pixel_format.four_c_c = pyffi.formats.dds.DdsFormat.FourCC.DXT5
                header.pixel_format.bit_count = 0
                header.pixel_format.r_mask = 0
                header.pixel_format.g_mask = 0
                header.pixel_format.b_mask = 0
                header.pixel_format.a_mask = 0
                header.caps_1.complex = 1
                header.caps_1.texture = 1
                header.caps_1.mipmap = 1
                pixeldata.set_value(''.join(self.pixel_data_matrix))
            else:
                raise ValueError(
                    "cannot save pixel format %i as DDS" % self.pixel_format)

            data.write(stream)

    class NiSkinData:
        def get_transform(self):
            """Return scale, rotation, and translation into a single 4x4 matrix."""
            mat = NifFormat.Matrix44()
            mat.set_scale_rotation_translation(self.scale, self.rotation, self.translation)
            return mat

        def set_transform(self, mat):
            """Set rotation, transform, and velocity."""
            scale, rotation, translation = mat.get_scale_rotation_translation()

            self.scale = scale

            self.rotation.m_11 = rotation.m_11
            self.rotation.m_12 = rotation.m_12
            self.rotation.m_13 = rotation.m_13
            self.rotation.m_21 = rotation.m_21
            self.rotation.m_22 = rotation.m_22
            self.rotation.m_23 = rotation.m_23
            self.rotation.m_31 = rotation.m_31
            self.rotation.m_32 = rotation.m_32
            self.rotation.m_33 = rotation.m_33

            self.translation.x = translation.x
            self.translation.y = translation.y
            self.translation.z = translation.z

        def apply_scale(self, scale):
            """Apply scale factor on data.

            >>> from pyffi.formats.nif import NifFormat
            >>> id44 = NifFormat.Matrix44()
            >>> id44.set_identity()
            >>> skelroot = NifFormat.NiNode()
            >>> skelroot.name = 'Scene Root'
            >>> skelroot.set_transform(id44)
            >>> bone1 = NifFormat.NiNode()
            >>> bone1.name = 'bone1'
            >>> bone1.set_transform(id44)
            >>> bone1.translation.x = 10
            >>> skelroot.add_child(bone1)
            >>> geom = NifFormat.NiTriShape()
            >>> geom.set_transform(id44)
            >>> skelroot.add_child(geom)
            >>> skininst = NifFormat.NiSkinInstance()
            >>> geom.skin_instance = skininst
            >>> skininst.skeleton_root = skelroot
            >>> skindata = NifFormat.NiSkinData()
            >>> skininst.data = skindata
            >>> skindata.set_transform(id44)
            >>> geom.add_bone(bone1, {})
            >>> geom.update_bind_position()
            >>> bone1.translation.x
            10.0
            >>> skindata.bone_list[0].translation.x
            -10.0
            >>> import pyffi.spells.nif.fix
            >>> import pyffi.spells.nif
            >>> data = NifFormat.Data()
            >>> data.roots = [skelroot]
            >>> toaster = pyffi.spells.nif.NifToaster()
            >>> toaster.scale = 0.1
            >>> pyffi.spells.nif.fix.SpellScale(data=data, toaster=toaster).recurse()
            pyffi.toaster:INFO:--- fix_scale ---
            pyffi.toaster:INFO:  scaling by factor 0.100000
            pyffi.toaster:INFO:  ~~~ NiNode [Scene Root] ~~~
            pyffi.toaster:INFO:    ~~~ NiNode [bone1] ~~~
            pyffi.toaster:INFO:    ~~~ NiTriShape [] ~~~
            pyffi.toaster:INFO:      ~~~ NiSkinInstance [] ~~~
            pyffi.toaster:INFO:        ~~~ NiSkinData [] ~~~
            >>> bone1.translation.x
            1.0
            >>> skindata.bone_list[0].translation.x
            -1.0
            """

            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale

            for skindata in self.bone_list:
                skindata.translation.x *= scale
                skindata.translation.y *= scale
                skindata.translation.z *= scale
                skindata.bounding_sphere_offset.x *= scale
                skindata.bounding_sphere_offset.y *= scale
                skindata.bounding_sphere_offset.z *= scale
                skindata.bounding_sphere_radius *= scale

    class NiTransformInterpolator:
        def apply_scale(self, scale):
            """Apply scale factor <scale> on data."""
            # apply scale on translation
            self.translation.x *= scale
            self.translation.y *= scale
            self.translation.z *= scale

    class NiTriBasedGeomData:
        def is_interchangeable(self, other):
            """Heuristically checks if two NiTriBasedGeomData blocks describe
            the same geometry, that is, if they can be used interchangeably in
            a nif file without affecting the rendering. The check is not fool
            proof but has shown to work in most practical cases.

            :param other: Another geometry data block.
            :type other: L{NifFormat.NiTriBasedGeomData} (if it has another type
                then the function will always return ``False``)
            :return: ``True`` if the geometries are equivalent, ``False`` otherwise.
            """
            # check for object identity
            if self is other:
                return True

            # type check
            if not isinstance(other, NifFormat.NiTriBasedGeomData):
                return False

            # check class
            if (not isinstance(self, other.__class__)
                or not isinstance(other, self.__class__)):
                return False

            # check some trivial things first
            for attribute in (
                "num_vertices", "keep_flags", "compress_flags", "has_vertices",
                "num_uv_sets", "has_normals", "center", "radius",
                "has_vertex_colors", "has_uv", "consistency_flags"):
                if getattr(self, attribute) != getattr(other, attribute):
                    return False

            # check vertices (this includes uvs, vcols and normals)
            verthashes1 = [hsh for hsh in self.get_vertex_hash_generator()]
            verthashes2 = [hsh for hsh in other.get_vertex_hash_generator()]
            for hash1 in verthashes1:
                if not hash1 in verthashes2:
                    return False
            for hash2 in verthashes2:
                if not hash2 in verthashes1:
                    return False

            # check triangle list
            triangles1 = [tuple(verthashes1[i] for i in tri)
                          for tri in self.get_triangles()]
            triangles2 = [tuple(verthashes2[i] for i in tri)
                          for tri in other.get_triangles()]
            for tri1 in triangles1:
                if not tri1 in triangles2:
                    return False
            for tri2 in triangles2:
                if not tri2 in triangles1:
                    return False

            # looks pretty identical!
            return True

        def get_triangle_indices(self, triangles):
            """Yield list of triangle indices (relative to
            self.get_triangles()) of given triangles. Degenerate triangles in
            the list are assigned index ``None``.

            >>> from pyffi.formats.nif import NifFormat
            >>> geomdata = NifFormat.NiTriShapeData()
            >>> geomdata.set_triangles([(0,1,2),(1,2,3),(2,3,4)])
            >>> list(geomdata.get_triangle_indices([(1,2,3)]))
            [1]
            >>> list(geomdata.get_triangle_indices([(3,1,2)]))
            [1]
            >>> list(geomdata.get_triangle_indices([(2,3,1)]))
            [1]
            >>> list(geomdata.get_triangle_indices([(1,2,0),(4,2,3)]))
            [0, 2]
            >>> list(geomdata.get_triangle_indices([(0,0,0),(4,2,3)]))
            [None, 2]
            >>> list(geomdata.get_triangle_indices([(0,3,4),(4,2,3)])) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...

            :param triangles: An iterable of triangles to check.
            :type triangles: iterator or list of tuples of three ints
            """
            def triangleHash(triangle):
                """Calculate hash of a non-degenerate triangle.
                Returns ``None`` if the triangle is degenerate.
                """
                if triangle[0] < triangle[1] and triangle[0] < triangle[2]:
                    return hash((triangle[0], triangle[1], triangle[2]))
                elif triangle[1] < triangle[0] and triangle[1] < triangle[2]:
                    return hash((triangle[1], triangle[2], triangle[0]))
                elif triangle[2] < triangle[0] and triangle[2] < triangle[1]:
                    return hash((triangle[2], triangle[0], triangle[1]))

            # calculate hashes of all triangles in the geometry
            self_triangles_hashes = [
                triangleHash(triangle) for triangle in self.get_triangles()]

            # calculate index of each triangle in the list of triangles
            for triangle in triangles:
                triangle_hash = triangleHash(triangle)
                if triangle_hash is None:
                    yield None
                else:
                    yield self_triangles_hashes.index(triangle_hash)

    class NiTriBasedGeom:
        def get_tangent_space(self):
            """Return iterator over normal, tangent, bitangent vectors.
            If the block has no tangent space, then returns None.
            """

            def bytes2vectors(data, pos, num):
                for i in xrange(num):
                    # data[pos:pos+12] is not really well implemented, so do this
                    vecdata = ''.join(data[j] for j in xrange(pos, pos + 12))
                    vec = NifFormat.Vector3()
                    # XXX _byte_order! assuming little endian
                    vec.x, vec.y, vec.z = struct.unpack('<fff', vecdata)
                    yield vec
                    pos += 12


            if self.data.num_vertices == 0:
                return ()

            if not self.data.normals:
                #raise ValueError('geometry has no normals')
                return None

            if (not self.data.tangents) or (not self.data.bitangents):
                # no tangents and bitangents at the usual location
                # perhaps there is Oblivion style data?
                for extra in self.get_extra_datas():
                    if isinstance(extra, NifFormat.NiBinaryExtraData):
                        if extra.name == 'Tangent space (binormal & tangent vectors)':
                            break
                else:
                    #raise ValueError('geometry has no tangents')
                    return None
                if 24 * self.data.num_vertices != len(extra.binary_data):
                    raise ValueError(
                        'tangent space data has invalid size, expected %i bytes but got %i'
                        % (24 * self.data.num_vertices, len(extra.binary_data)))
                tangents = bytes2vectors(extra.binary_data,
                                         0,
                                         self.data.num_vertices)
                bitangents = bytes2vectors(extra.binary_data,
                                           12 * self.data.num_vertices,
                                           self.data.num_vertices)
            else:
                tangents = self.data.tangents
                bitangents = self.data.bitangents

            return izip(self.data.normals, tangents, bitangents)

        def update_tangent_space(
            self, as_extra=None,
            vertexprecision=3, normalprecision=3):
            """Recalculate tangent space data.

            :param as_extra: Whether to store the tangent space data as extra data
                (as in Oblivion) or not (as in Fallout 3). If not set, switches to
                Oblivion if an extra data block is found, otherwise does default.
                Set it to override this detection (for example when using this
                function to create tangent space data) and force behaviour.
            """
            # check that self.data exists and is valid
            if not isinstance(self.data, NifFormat.NiTriBasedGeomData):
                raise ValueError(
                    'cannot update tangent space of a geometry with %s data'
                    %(self.data.__class__ if self.data else 'no'))

            verts = self.data.vertices
            norms = self.data.normals
            if len(self.data.uv_sets) > 0:
                uvs   = self.data.uv_sets[0]
            else:
                # no uv sets so no tangent space
                # we clear the tangents space flag just
                # happens in Fallout NV
                # meshes/architecture/bouldercity/arcadeendl.nif
                # (see issue #3218751)
                self.data.num_uv_sets &= ~4096
                self.data.bs_num_uv_sets &= ~4096
                return

            # check that shape has norms and uvs
            if len(uvs) == 0 or len(norms) == 0: return

            # identify identical (vertex, normal) pairs to avoid issues along
            # uv seams due to vertex duplication
            # implementation note: uvprecision and vcolprecision 0
            # should be enough, but use -2 just to be really sure
            # that this is ignored
            v_hash_map = list(
                self.data.get_vertex_hash_generator(
                    vertexprecision=vertexprecision,
                    normalprecision=normalprecision,
                    uvprecision=-2,
                    vcolprecision=-2))

            # tangent and binormal dictionaries by vertex hash
            bin = dict((h, NifFormat.Vector3()) for h in v_hash_map)
            tan = dict((h, NifFormat.Vector3()) for h in v_hash_map)

            # calculate tangents and binormals from vertex and texture coordinates
            for t1, t2, t3 in self.data.get_triangles():
                # find hash values
                h1 = v_hash_map[t1]
                h2 = v_hash_map[t2]
                h3 = v_hash_map[t3]
                # skip degenerate triangles
                if h1 == h2 or h2 == h3 or h3 == h1:
                    continue

                v_1 = verts[t1]
                v_2 = verts[t2]
                v_3 = verts[t3]
                w1 = uvs[t1]
                w2 = uvs[t2]
                w3 = uvs[t3]
                v_2v_1 = v_2 - v_1
                v_3v_1 = v_3 - v_1
                w2w1 = w2 - w1
                w3w1 = w3 - w1

                # surface of triangle in texture space
                r = w2w1.u * w3w1.v - w3w1.u * w2w1.v

                # sign of surface
                r_sign = (1 if r >= 0 else -1)

                # contribution of this triangle to tangents and binormals
                sdir = NifFormat.Vector3()
                sdir.x = (w3w1.v * v_2v_1.x - w2w1.v * v_3v_1.x) * r_sign
                sdir.y = (w3w1.v * v_2v_1.y - w2w1.v * v_3v_1.y) * r_sign
                sdir.z = (w3w1.v * v_2v_1.z - w2w1.v * v_3v_1.z) * r_sign
                try:
                    sdir.normalize()
                except ZeroDivisionError: # catches zero vector
                    continue # skip triangle
                except ValueError: # catches invalid data
                    continue # skip triangle

                tdir = NifFormat.Vector3()
                tdir.x = (w2w1.u * v_3v_1.x - w3w1.u * v_2v_1.x) * r_sign
                tdir.y = (w2w1.u * v_3v_1.y - w3w1.u * v_2v_1.y) * r_sign
                tdir.z = (w2w1.u * v_3v_1.z - w3w1.u * v_2v_1.z) * r_sign
                try:
                    tdir.normalize()
                except ZeroDivisionError: # catches zero vector
                    continue # skip triangle
                except ValueError: # catches invalid data
                    continue # skip triangle

                # vector combination algorithm could possibly be improved
                for h in [h1, h2, h3]:
                    # addition inlined for speed
                    tanh = tan[h]
                    tanh.x += tdir.x
                    tanh.y += tdir.y
                    tanh.z += tdir.z
                    binh = bin[h]
                    binh.x += sdir.x
                    binh.y += sdir.y
                    binh.z += sdir.z

            xvec = NifFormat.Vector3()
            xvec.x = 1.0
            xvec.y = 0.0
            xvec.z = 0.0
            yvec = NifFormat.Vector3()
            yvec.x = 0.0
            yvec.y = 1.0
            yvec.z = 0.0
            for n, h in izip(norms, v_hash_map):
                binh = bin[h]
                tanh = tan[h]
                try:
                    n.normalize()
                except (ValueError, ZeroDivisionError):
                    # this happens if the normal has NAN values or is zero
                    # just pick something in that case
                    n = yvec
                try:
                    # turn n, bin, tan into a base via Gram-Schmidt
                    # bin[h] -= n * (n * bin[h])
                    # inlined for speed
                    scalar = n * binh
                    binh.x -= n.x * scalar
                    binh.y -= n.y * scalar
                    binh.z -= n.z * scalar
                    binh.normalize()

                    # tan[h] -= n * (n * tan[h])
                    # tan[h] -= bin[h] * (bin[h] * tan[h])
                    # inlined for speed
                    scalar = n * tanh
                    tanh.x -= n.x * scalar
                    tanh.y -= n.y * scalar
                    tanh.z -= n.z * scalar
                    
                    scalar = binh * tanh
                    tanh.x -= binh.x * scalar
                    tanh.y -= binh.y * scalar
                    tanh.z -= binh.z * scalar
                    tanh.normalize()
                except ZeroDivisionError:
                    # insuffient data to set tangent space for this vertex
                    # in that case pick a space
                    binh = xvec.crossproduct(n)
                    try:
                        binh.normalize()
                    except ZeroDivisionError:
                        binh = yvec.crossproduct(n)
                        binh.normalize() # should work now
                    tanh = n.crossproduct(binh)

            # tangent and binormal lists by vertex index
            tan = [tan[h] for h in v_hash_map]
            bin = [bin[h] for h in v_hash_map]

            # find possible extra data block
            for extra in self.get_extra_datas():
                if isinstance(extra, NifFormat.NiBinaryExtraData):
                    if extra.name == 'Tangent space (binormal & tangent vectors)':
                        break
            else:
                extra = None

            # if autodetection is on, do as_extra only if an extra data block is found
            if as_extra is None:
                if extra:
                    as_extra = True
                else:
                    as_extra = False

            if as_extra:
                # if tangent space extra data already exists, use it
                if not extra:
                    # otherwise, create a new block and link it
                    extra = NifFormat.NiBinaryExtraData()
                    extra.name = 'Tangent space (binormal & tangent vectors)'
                    self.add_extra_data(extra)

                # write the data
                binarydata = ""
                for vec in tan + bin:
                    # XXX _byte_order!! assuming little endian
                    binarydata += struct.pack('<fff', vec.x, vec.y, vec.z)
                extra.binary_data = binarydata
            else:
                # set tangent space flag
                # XXX used to be 61440
                # XXX from Sid Meier's Railroad & Fallout 3 nifs, 4096 is
                # XXX sufficient?
                self.data.num_uv_sets |= 4096
                self.data.bs_num_uv_sets |= 4096
                self.data.tangents.update_size()
                self.data.bitangents.update_size()
                for vec, data_tan in izip(tan, self.data.tangents):
                    data_tan.x = vec.x
                    data_tan.y = vec.y
                    data_tan.z = vec.z
                for vec, data_bitan in izip(bin, self.data.bitangents):
                    data_bitan.x = vec.x
                    data_bitan.y = vec.y
                    data_bitan.z = vec.z

        # ported from nifskope/skeleton.cpp:spSkinPartition
        def update_skin_partition(self,
                                maxbonesperpartition=4, maxbonespervertex=4,
                                verbose=0, stripify=True, stitchstrips=False,
                                padbones=False,
                                triangles=None, trianglepartmap=None,
                                maximize_bone_sharing=False):
            """Recalculate skin partition data.

            :deprecated: Do not use the verbose argument.
            :param maxbonesperpartition: Maximum number of bones in each partition.
                The num_bones field will not exceed this number.
            :param maxbonespervertex: Maximum number of bones per vertex.
                The num_weights_per_vertex field will be exactly equal to this number.
            :param verbose: Ignored, and deprecated. Set pyffi's log level instead.
            :param stripify: If true, stripify the partitions, otherwise use triangles.
            :param stitchstrips: If stripify is true, then set this to true to stitch
                the strips.
            :param padbones: Enforces the numbones field to be equal to
                maxbonesperpartition. Also ensures that the bone indices are unique
                and sorted, per vertex. Raises an exception if maxbonespervertex
                is not equal to maxbonesperpartition (in that case bone indices cannot
                be unique and sorted). This options is required for Freedom Force vs.
                the 3rd Reich skin partitions.
            :param triangles: The triangles of the partition (if not specified, then
                this defaults to C{self.data.get_triangles()}.
            :param trianglepartmap: Maps each triangle to a partition index. Faces with
                different indices will never appear in the same partition. If the skin
                instance is a BSDismemberSkinInstance, then these indices are used as
                body part types, and the partitions in the BSDismemberSkinInstance are
                updated accordingly. Note that the faces are counted relative to
                L{triangles}.
            :param maximize_bone_sharing: Maximize bone sharing between partitions.
                This option is useful for Fallout 3.
            """
            logger = logging.getLogger("pyffi.nif.nitribasedgeom")

            # if trianglepartmap not specified, map everything to index 0
            if trianglepartmap is None:
                trianglepartmap = repeat(0)

            # shortcuts relevant blocks
            if not self.skin_instance:
                # no skin, nothing to do
                return
            self._validate_skin()
            geomdata = self.data
            skininst = self.skin_instance
            skindata = skininst.data

            # get skindata vertex weights
            logger.debug("Getting vertex weights.")
            weights = self.get_vertex_weights()

            # count minimum and maximum number of bones per vertex
            minbones = min(len(weight) for weight in weights)
            maxbones = max(len(weight) for weight in weights)
            if minbones <= 0:
                noweights = [v for v, weight in enumerate(weights)
                             if not weight]
                #raise ValueError(
                logger.warn(
                    'bad NiSkinData: some vertices have no weights %s'
                    % noweights)
            logger.info("Counted minimum of %i and maximum of %i bones per vertex"
                        % (minbones, maxbones))

            # reduce bone influences to meet maximum number of bones per vertex
            logger.info("Imposing maximum of %i bones per vertex." % maxbonespervertex)
            lostweight = 0.0
            for weight in weights:
                if len(weight) > maxbonespervertex:
                    # delete bone influences with least weight
                    weight.sort(key=lambda x: x[1], reverse=True) # sort by weight
                    # save lost weight to return to user
                    lostweight = max(
                        lostweight, max(
                            [x[1] for x in weight[maxbonespervertex:]]))
                    del weight[maxbonespervertex:] # only keep first elements
                    # normalize
                    totalweight = sum([x[1] for x in weight]) # sum of all weights
                    for x in weight: x[1] /= totalweight
                    maxbones = maxbonespervertex
                # sort by again by bone (relied on later when matching vertices)
                weight.sort(key=lambda x: x[0])

            # reduce bone influences to meet maximum number of bones per partition
            # (i.e. maximum number of bones per triangle)
            logger.info(
                "Imposing maximum of %i bones per triangle (and hence, per partition)."
                % maxbonesperpartition)

            if triangles is None:
                triangles = geomdata.get_triangles()

            for tri in triangles:
                while True:
                    # find the bones influencing this triangle
                    tribones = []
                    for t in tri:
                        tribones.extend([bonenum for bonenum, boneweight in weights[t]])
                    tribones = set(tribones)
                    # target met?
                    if len(tribones) <= maxbonesperpartition:
                        break
                    # no, need to remove a bone

                    # sum weights for each bone to find the one that least influences
                    # this triangle
                    tribonesweights = {}
                    for bonenum in tribones: tribonesweights[bonenum] = 0.0
                    nono = set() # bones with weight 1 cannot be removed
                    for skinweights in [weights[t] for t in tri]:
                        # skinweights[0] is the first skinweight influencing vertex t
                        # and skinweights[0][0] is the bone number of that bone
                        if len(skinweights) == 1: nono.add(skinweights[0][0])
                        for bonenum, boneweight in skinweights:
                            tribonesweights[bonenum] += boneweight

                    # select a bone to remove
                    # first find bones we can remove

                    # restrict to bones not in the nono set
                    tribonesweights = [
                        x for x in tribonesweights.items() if x[0] not in nono]
                    if not tribonesweights:
                        raise ValueError(
                            "cannot remove anymore bones in this skin; "
                            "increase maxbonesperpartition and try again")
                    # sort by vertex weight sum the last element of this list is now a
                    # candidate for removal
                    tribonesweights.sort(key=lambda x: x[1], reverse=True)
                    minbone = tribonesweights[-1][0]

                    # remove minbone from all vertices of this triangle and from all
                    # matching vertices
                    for t in tri:
                        for tt in [t]: #match[t]:
                            # remove bone
                            weight = weights[tt]
                            for i, (bonenum, boneweight) in enumerate(weight):
                                if bonenum == minbone:
                                    # save lost weight to return to user
                                    lostweight = max(lostweight, boneweight)
                                    del weight[i]
                                    break
                            else:
                                continue
                            # normalize
                            totalweight = sum([x[1] for x in weight])
                            for x in weight:
                                x[1] /= totalweight

            # split triangles into partitions
            logger.info("Creating partitions")
            parts = []
            # keep creating partitions as long as there are triangles left
            while triangles:
                # create a partition
                part = [set(), [], None] # bones, triangles, partition index
                usedverts = set()
                addtriangles = True
                # keep adding triangles to it as long as the flag is set
                while addtriangles:
                    # newtriangles is a list of triangles that have not been added to
                    # the partition, similar for newtrianglepartmap
                    newtriangles = []
                    newtrianglepartmap = []
                    for tri, partindex in izip(triangles, trianglepartmap):
                        # find the bones influencing this triangle
                        tribones = []
                        for t in tri:
                            tribones.extend([
                                bonenum for bonenum, boneweight in weights[t]])
                        tribones = set(tribones)
                        # if part has no bones,
                        # or if part has all bones of tribones and index coincides
                        # then add this triangle to this part
                        if ((not part[0])
                            or ((part[0] >= tribones) and (part[2] == partindex))):
                            part[0] |= tribones
                            part[1].append(tri)
                            usedverts |= set(tri)
                            # if part was empty, assign it the index
                            if part[2] is None:
                                part[2] = partindex
                        else:
                            newtriangles.append(tri)
                            newtrianglepartmap.append(partindex)
                    triangles = newtriangles
                    trianglepartmap = newtrianglepartmap

                    # if we have room left in the partition
                    # then add adjacent triangles
                    addtriangles = False
                    newtriangles = []
                    newtrianglepartmap = []
                    if len(part[0]) < maxbonesperpartition:
                        for tri, partindex in izip(triangles, trianglepartmap):
                            # if triangle is adjacent, and has same index
                            # then check if it can be added to the partition
                            if (usedverts & set(tri)) and (part[2] == partindex):
                                # find the bones influencing this triangle
                                tribones = []
                                for t in tri:
                                    tribones.extend([
                                        bonenum for bonenum, boneweight in weights[t]])
                                tribones = set(tribones)
                                # and check if we exceed the maximum number of allowed
                                # bones
                                if len(part[0] | tribones) <= maxbonesperpartition:
                                    part[0] |= tribones
                                    part[1].append(tri)
                                    usedverts |= set(tri)
                                    # signal another try in adding triangles to
                                    # the partition
                                    addtriangles = True
                                else:
                                    newtriangles.append(tri)
                                    newtrianglepartmap.append(partindex)
                            else:
                                newtriangles.append(tri)
                                newtrianglepartmap.append(partindex)
                        triangles = newtriangles
                        trianglepartmap = newtrianglepartmap

                parts.append(part)

            logger.info("Created %i small partitions." % len(parts))

            # merge all partitions
            logger.info("Merging partitions.")
            merged = True # signals success, in which case do another run
            while merged:
                merged = False
                # newparts is to contain the updated merged partitions as we go
                newparts = []
                # addedparts is the set of all partitions from parts that have been
                # added to newparts
                addedparts = set()
                # try all combinations
                for a, parta in enumerate(parts):
                    if a in addedparts:
                        continue
                    newparts.append(parta)
                    addedparts.add(a)
                    for b, partb in enumerate(parts):
                        if b <= a:
                            continue
                        if b in addedparts:
                            continue
                        # if partition indices are the same, and bone limit is not
                        # exceeded, merge them
                        if ((parta[2] == partb[2])
                            and (len(parta[0] | partb[0]) <= maxbonesperpartition)):
                            parta[0] |= partb[0]
                            parta[1] += partb[1]
                            addedparts.add(b)
                            merged = True # signal another try in merging partitions
                # update partitions to the merged partitions
                parts = newparts

            # write the NiSkinPartition
            logger.info("Skin has %i partitions." % len(parts))

            # if skin partition already exists, use it
            if skindata.skin_partition != None:
                skinpart = skindata.skin_partition
                skininst.skin_partition = skinpart
            elif skininst.skin_partition != None:
                skinpart = skininst.skin_partition
                skindata.skin_partition = skinpart
            else:
            # otherwise, create a new block and link it
                skinpart = NifFormat.NiSkinPartition()
                skindata.skin_partition = skinpart
                skininst.skin_partition = skinpart

            # set number of partitions
            skinpart.num_skin_partition_blocks = len(parts)
            skinpart.skin_partition_blocks.update_size()

            # maximize bone sharing, if requested
            if maximize_bone_sharing:
                logger.info("Maximizing shared bones.")
                # new list of partitions, sorted to maximize bone sharing
                newparts = []
                # as long as there are parts to add
                while parts:
                    # current set of partitions with shared bones
                    # starts a new set of partitions with shared bones
                    sharedparts = [parts.pop()]
                    sharedboneset = sharedparts[0][0]
                    # go over all other partitions, and try to add them with
                    # shared bones
                    oldparts = parts[:]
                    parts = []
                    for otherpart in oldparts:
                        # check if bones can be added
                        if len(sharedboneset | otherpart[0]) <= maxbonesperpartition:
                            # ok, we can share bones!
                            # update set of shared bones
                            sharedboneset |= otherpart[0]
                            # add this other partition to list of shared parts
                            sharedparts.append(otherpart)
                            # update bone set in all shared parts
                            for sharedpart in sharedparts:
                                sharedpart[0] = sharedboneset
                        else:
                            # not added to sharedparts,
                            # so we must keep it for the next iteration
                            parts.append(otherpart)
                    # update list of partitions
                    newparts.extend(sharedparts)

                # store update
                parts = newparts

            # for Fallout 3, set dismember partition indices
            if isinstance(skininst, NifFormat.BSDismemberSkinInstance):
                skininst.num_partitions = len(parts)
                skininst.partitions.update_size()
                lastpart = None
                for bodypart, part in izip(skininst.partitions, parts):
                    bodypart.body_part = part[2]
                    if (lastpart is None) or (lastpart[0] != part[0]):
                        # start new bone set, if bones are not shared
                        bodypart.part_flag.start_new_boneset = 1
                    else:
                        # do not start new bone set
                        bodypart.part_flag.start_new_boneset = 0
                    # caps are invisible
                    bodypart.part_flag.editor_visible = (part[2] < 100
                                                         or part[2] >= 1000)
                    # store part for next iteration
                    lastpart = part

            for skinpartblock, part in zip(skinpart.skin_partition_blocks, parts):
                # get sorted list of bones
                bones = sorted(list(part[0]))
                triangles = part[1]
                logger.info("Optimizing triangle ordering in partition %i"
                            % parts.index(part))
                # optimize triangles for vertex cache and calculate strips
                triangles = pyffi.utils.vertex_cache.get_cache_optimized_triangles(
                    triangles)
                strips = pyffi.utils.vertex_cache.stable_stripify(
                    triangles, stitchstrips=stitchstrips)
                triangles_size = 3 * len(triangles)
                strips_size = len(strips) + sum(len(strip) for strip in strips)
                vertices = []
                # decide whether to use strip or triangles as primitive
                if stripify is None:
                    stripifyblock = (
                        strips_size < triangles_size
                        and all(len(strip) < 65536 for strip in strips))
                else:
                    stripifyblock = stripify
                if stripifyblock:
                    # stripify the triangles
                    # also update triangle list
                    numtriangles = 0
                    # calculate number of triangles and get sorted
                    # list of vertices
                    # for optimal performance, vertices must be sorted
                    # by strip
                    for strip in strips:
                        numtriangles += len(strip) - 2
                        for t in strip:
                            if t not in vertices:
                                vertices.append(t)
                else:
                    numtriangles = len(triangles)
                    # get sorted list of vertices
                    # for optimal performance, vertices must be sorted
                    # by triangle
                    for tri in triangles:
                        for t in tri:
                            if t not in vertices:
                                vertices.append(t)
                # set all the data
                skinpartblock.num_vertices = len(vertices)
                skinpartblock.num_triangles = numtriangles
                if not padbones:
                    skinpartblock.num_bones = len(bones)
                else:
                    if maxbonesperpartition != maxbonespervertex:
                        raise ValueError(
                            "when padding bones maxbonesperpartition must be "
                            "equal to maxbonespervertex")
                    # freedom force vs. the 3rd reich needs exactly 4 bones per
                    # partition on every partition block
                    skinpartblock.num_bones = maxbonesperpartition
                if stripifyblock:
                    skinpartblock.num_strips = len(strips)
                else:
                    skinpartblock.num_strips = 0
                # maxbones would be enough as num_weights_per_vertex but the Gamebryo
                # engine doesn't like that, it seems to want exactly 4 even if there
                # are fewer
                skinpartblock.num_weights_per_vertex = maxbonespervertex
                skinpartblock.bones.update_size()
                for i, bonenum in enumerate(bones):
                    skinpartblock.bones[i] = bonenum
                for i in xrange(len(bones), skinpartblock.num_bones):
                    skinpartblock.bones[i] = 0 # dummy bone slots refer to first bone
                skinpartblock.has_vertex_map = True
                skinpartblock.vertex_map.update_size()
                for i, v in enumerate(vertices):
                    skinpartblock.vertex_map[i] = v
                skinpartblock.has_vertex_weights = True
                skinpartblock.vertex_weights.update_size()
                for i, v in enumerate(vertices):
                    for j in xrange(skinpartblock.num_weights_per_vertex):
                        if j < len(weights[v]):
                            skinpartblock.vertex_weights[i][j] = weights[v][j][1]
                        else:
                            skinpartblock.vertex_weights[i][j] = 0.0
                if stripifyblock:
                    skinpartblock.has_faces = True
                    skinpartblock.strip_lengths.update_size()
                    for i, strip in enumerate(strips):
                        skinpartblock.strip_lengths[i] = len(strip)
                    skinpartblock.strips.update_size()
                    for i, strip in enumerate(strips):
                        for j, v in enumerate(strip):
                            skinpartblock.strips[i][j] = vertices.index(v)
                else:
                    skinpartblock.has_faces = True
                    # clear strip lengths array
                    skinpartblock.strip_lengths.update_size()
                    # clear strips array
                    skinpartblock.strips.update_size()
                    skinpartblock.triangles.update_size()
                    for i, (v_1,v_2,v_3) in enumerate(triangles):
                        skinpartblock.triangles[i].v_1 = vertices.index(v_1)
                        skinpartblock.triangles[i].v_2 = vertices.index(v_2)
                        skinpartblock.triangles[i].v_3 = vertices.index(v_3)
                skinpartblock.has_bone_indices = True
                skinpartblock.bone_indices.update_size()
                for i, v in enumerate(vertices):
                    # the boneindices set keeps track of indices that have not been
                    # used yet
                    boneindices = set(range(skinpartblock.num_bones))
                    for j in xrange(len(weights[v])):
                        skinpartblock.bone_indices[i][j] = bones.index(weights[v][j][0])
                        boneindices.remove(skinpartblock.bone_indices[i][j])
                    for j in xrange(len(weights[v]),skinpartblock.num_weights_per_vertex):
                        if padbones:
                            # if padbones is True then we have enforced
                            # num_bones == num_weights_per_vertex so this will not trigger
                            # a KeyError
                            skinpartblock.bone_indices[i][j] = boneindices.pop()
                        else:
                            skinpartblock.bone_indices[i][j] = 0

                # sort weights
                for i, v in enumerate(vertices):
                    vweights = []
                    for j in xrange(skinpartblock.num_weights_per_vertex):
                        vweights.append([
                            skinpartblock.bone_indices[i][j],
                            skinpartblock.vertex_weights[i][j]])
                    if padbones:
                        # by bone index (for ffvt3r)
                        vweights.sort(key=lambda w: w[0])
                    else:
                        # by weight (for fallout 3, largest weight first)
                        vweights.sort(key=lambda w: -w[1])
                    for j in xrange(skinpartblock.num_weights_per_vertex):
                        skinpartblock.bone_indices[i][j] = vweights[j][0]
                        skinpartblock.vertex_weights[i][j] = vweights[j][1]

            return lostweight

        # ported from nifskope/skeleton.cpp:spFixBoneBounds
        def update_skin_center_radius(self):
            """Update centers and radii of all skin data fields."""
            # shortcuts relevant blocks
            if not self.skin_instance:
                return # no skin, nothing to do
            self._validate_skin()
            geomdata = self.data
            skininst = self.skin_instance
            skindata = skininst.data

            verts = geomdata.vertices

            for skindatablock in skindata.bone_list:
                # find all vertices influenced by this bone
                boneverts = [verts[skinweight.index]
                             for skinweight in skindatablock.vertex_weights]

                # find bounding box of these vertices
                low = NifFormat.Vector3()
                low.x = min(v.x for v in boneverts)
                low.y = min(v.y for v in boneverts)
                low.z = min(v.z for v in boneverts)

                high = NifFormat.Vector3()
                high.x = max(v.x for v in boneverts)
                high.y = max(v.y for v in boneverts)
                high.z = max(v.z for v in boneverts)

                # center is in the center of the bounding box
                center = (low + high) * 0.5

                # radius is the largest distance from the center
                r2 = 0.0
                for v in boneverts:
                    d = center - v
                    r2 = max(r2, d.x*d.x+d.y*d.y+d.z*d.z)
                radius = r2 ** 0.5

                # transform center in proper coordinates (radius remains unaffected)
                center *= skindatablock.get_transform()

                # save data
                skindatablock.bounding_sphere_offset.x = center.x
                skindatablock.bounding_sphere_offset.y = center.y
                skindatablock.bounding_sphere_offset.z = center.z
                skindatablock.bounding_sphere_radius = radius

        def get_interchangeable_tri_shape(self, triangles=None):
            """Returns a NiTriShape block that is geometrically
            interchangeable. If you do not want to set the triangles
            from the original shape, use the triangles argument.
            """
            # copy the shape (first to NiTriBasedGeom and then to NiTriShape)
            shape = NifFormat.NiTriShape().deepcopy(
                NifFormat.NiTriBasedGeom().deepcopy(self))
            # copy the geometry without strips
            shapedata = NifFormat.NiTriShapeData().deepcopy(
                NifFormat.NiTriBasedGeomData().deepcopy(self.data))
            # update the shape data
            if triangles is None:
                shapedata.set_triangles(self.data.get_triangles())
            else:
                shapedata.set_triangles(triangles)
            # relink the shape data
            shape.data = shapedata
            # and return the result
            return shape

        def get_interchangeable_tri_strips(self, strips=None):
            """Returns a NiTriStrips block that is geometrically
            interchangeable.  If you do not want to set the strips
            from the original shape, use the strips argument.
            """
            # copy the shape (first to NiTriBasedGeom and then to NiTriStrips)
            strips_ = NifFormat.NiTriStrips().deepcopy(
                NifFormat.NiTriBasedGeom().deepcopy(self))
            # copy the geometry without triangles
            stripsdata = NifFormat.NiTriStripsData().deepcopy(
                NifFormat.NiTriBasedGeomData().deepcopy(self.data))
            # update the shape data
            if strips is None:
                stripsdata.set_strips(self.data.get_strips())
            else:
                stripsdata.set_strips(strips)
            # relink the shape data
            strips_.data = stripsdata
            # and return the result
            return strips_

    class NiTriShapeData:
        """
        Example usage:

        >>> from pyffi.formats.nif import NifFormat
        >>> block = NifFormat.NiTriShapeData()
        >>> block.set_triangles([(0,1,2),(2,1,3),(2,3,4)])
        >>> block.get_strips()
        [[0, 1, 2, 3, 4]]
        >>> block.get_triangles()
        [(0, 1, 2), (2, 1, 3), (2, 3, 4)]
        >>> block.set_strips([[1,0,1,2,3,4]])
        >>> block.get_strips() # stripifier keeps geometry but nothing else
        [[0, 2, 1, 3], [2, 4, 3]]
        >>> block.get_triangles()
        [(0, 2, 1), (1, 2, 3), (2, 4, 3)]
        """
        def get_triangles(self):
            return [(t.v_1, t.v_2, t.v_3) for t in self.triangles]

        def set_triangles(self, triangles, stitchstrips = False):
            # note: the stitchstrips argument is ignored - only present to ensure
            # uniform interface between NiTriShapeData and NiTriStripsData

            # initialize triangle array
            n = len(triangles)
            self.num_triangles = n
            self.num_triangle_points = 3*n
            self.has_triangles = (n > 0)
            self.triangles.update_size()

            # copy triangles
            src = triangles.__iter__()
            dst = self.triangles.__iter__()
            for k in xrange(n):
                dst_t = dst.next()
                dst_t.v_1, dst_t.v_2, dst_t.v_3 = src.next()

        def get_strips(self):
            return pyffi.utils.vertex_cache.stripify(self.get_triangles())

        def set_strips(self, strips):
            self.set_triangles(pyffi.utils.tristrip.triangulate(strips))

    class NiTriStripsData:
        """
        Example usage:

        >>> from pyffi.formats.nif import NifFormat
        >>> block = NifFormat.NiTriStripsData()
        >>> block.set_triangles([(0,1,2),(2,1,3),(2,3,4)])
        >>> block.get_strips()
        [[0, 1, 2, 3, 4]]
        >>> block.get_triangles()
        [(0, 1, 2), (1, 3, 2), (2, 3, 4)]
        >>> block.set_strips([[1,0,1,2,3,4]])
        >>> block.get_strips()
        [[1, 0, 1, 2, 3, 4]]
        >>> block.get_triangles()
        [(0, 2, 1), (1, 2, 3), (2, 4, 3)]
        """
        def get_triangles(self):
            return pyffi.utils.tristrip.triangulate(self.points)

        def set_triangles(self, triangles, stitchstrips = False):
            self.set_strips(pyffi.utils.vertex_cache.stripify(
                triangles, stitchstrips=stitchstrips))

        def get_strips(self):
            return [[i for i in strip] for strip in self.points]

        def set_strips(self, strips):
            # initialize strips array
            self.num_strips = len(strips)
            self.strip_lengths.update_size()
            numtriangles = 0
            for i, strip in enumerate(strips):
                self.strip_lengths[i] = len(strip)
                numtriangles += len(strip) - 2
            self.num_triangles = numtriangles
            self.points.update_size()
            self.has_points = (len(strips) > 0)

            # copy strips
            for i, strip in enumerate(strips):
                for j, idx in enumerate(strip):
                    self.points[i][j] = idx

    class RagdollDescriptor:
        def update_a_b(self, transform):
            """Update B pivot and axes from A using the given transform."""
            # pivot point
            pivot_b = ((7 * self.pivot_a.get_vector_3()) * transform) / 7.0
            self.pivot_b.x = pivot_b.x
            self.pivot_b.y = pivot_b.y
            self.pivot_b.z = pivot_b.z
            # axes (rotation only)
            transform = transform.get_matrix_33()
            plane_b = self.plane_a.get_vector_3() *  transform
            twist_b = self.twist_a.get_vector_3() *  transform
            self.plane_b.x = plane_b.x
            self.plane_b.y = plane_b.y
            self.plane_b.z = plane_b.z
            self.twist_b.x = twist_b.x
            self.twist_b.y = twist_b.y
            self.twist_b.z = twist_b.z

    class SkinData:
        def get_transform(self):
            """Return scale, rotation, and translation into a single 4x4 matrix."""
            m = NifFormat.Matrix44()
            m.set_scale_rotation_translation(self.scale, self.rotation, self.translation)
            return m

        def set_transform(self, m):
            """Set rotation, transform, and velocity."""
            scale, rotation, translation = m.get_scale_rotation_translation()

            self.scale = scale

            self.rotation.m_11 = rotation.m_11
            self.rotation.m_12 = rotation.m_12
            self.rotation.m_13 = rotation.m_13
            self.rotation.m_21 = rotation.m_21
            self.rotation.m_22 = rotation.m_22
            self.rotation.m_23 = rotation.m_23
            self.rotation.m_31 = rotation.m_31
            self.rotation.m_32 = rotation.m_32
            self.rotation.m_33 = rotation.m_33

            self.translation.x = translation.x
            self.translation.y = translation.y
            self.translation.z = translation.z

    class StringPalette:
        def get_string(self, offset):
            """Return string at given offset.

            >>> from pyffi.formats.nif import NifFormat
            >>> pal = NifFormat.StringPalette()
            >>> pal.add_string("abc")
            0
            >>> pal.add_string("def")
            4
            >>> print(pal.get_string(0).decode("ascii"))
            abc
            >>> print(pal.get_string(4).decode("ascii"))
            def
            >>> pal.get_string(5) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
            >>> pal.get_string(100) # doctest: +ELLIPSIS
            Traceback (most recent call last):
                ...
            ValueError: ...
            """
            _b00 = pyffi.object_models.common._b00 # shortcut
            # check that offset isn't too large
            if offset >= len(self.palette):
                raise ValueError(
                    "StringPalette: getting string at %i "
                    "but palette is only %i long"
                    % (offset, len(self.palette)))
            # check that a string starts at this offset
            if offset > 0 and self.palette[offset-1:offset] != _b00:
                raise ValueError(
                    "StringPalette: no string starts at offset %i "
                    "(palette is %s)" % (offset, self.palette))
            # return the string
            return self.palette[offset:self.palette.find(_b00, offset)]

        def get_all_strings(self):
            """Return a list of all strings.

            >>> from pyffi.formats.nif import NifFormat
            >>> pal = NifFormat.StringPalette()
            >>> pal.add_string("abc")
            0
            >>> pal.add_string("def")
            4
            >>> for x in pal.get_all_strings():
            ...     print(x.decode("ascii"))
            abc
            def
            >>> # pal.palette.decode("ascii") needs lstrip magic for py3k
            >>> print(repr(pal.palette.decode("ascii")).lstrip("u"))
            'abc\\x00def\\x00'
            """
            _b00 = pyffi.object_models.common._b00 # shortcut
            return self.palette[:-1].split(_b00)

        def add_string(self, text):
            """Adds string to palette (will recycle existing strings if possible) and
            return offset to the string in the palette.

            >>> from pyffi.formats.nif import NifFormat
            >>> pal = NifFormat.StringPalette()
            >>> pal.add_string("abc")
            0
            >>> pal.add_string("abc")
            0
            >>> pal.add_string("def")
            4
            >>> pal.add_string("")
            -1
            >>> print(pal.get_string(4).decode("ascii"))
            def
            """
            # empty text
            if not text:
                return -1
            _b00 = pyffi.object_models.common._b00 # shortcut
            # convert text to bytes if necessary
            text = pyffi.object_models.common._as_bytes(text)
            # check if string is already in the palette
            # ... at the start
            if text + _b00 == self.palette[:len(text) + 1]:
                return 0
            # ... or elsewhere
            offset = self.palette.find(_b00 + text + _b00)
            if offset != -1:
                return offset + 1
            # if no match, add the string
            if offset == -1:
                offset = len(self.palette)
                self.palette = self.palette + text + _b00
                self.length += len(text) + 1
            # return the offset
            return offset

        def clear(self):
            """Clear all strings in the palette.

            >>> from pyffi.formats.nif import NifFormat
            >>> pal = NifFormat.StringPalette()
            >>> pal.add_string("abc")
            0
            >>> pal.add_string("def")
            4
            >>> # pal.palette.decode("ascii") needs lstrip magic for py3k
            >>> print(repr(pal.palette.decode("ascii")).lstrip("u"))
            'abc\\x00def\\x00'
            >>> pal.clear()
            >>> # pal.palette.decode("ascii") needs lstrip magic for py3k
            >>> print(repr(pal.palette.decode("ascii")).lstrip("u"))
            ''
            """
            self.palette = pyffi.object_models.common._b # empty bytes object
            self.length = 0

    class TexCoord:
        def as_list(self):
            return [self.u, self.v]

        def normalize(self):
            r = (self.u*self.u + self.v*self.v) ** 0.5
            if r < NifFormat.EPSILON:
                raise ZeroDivisionError('cannot normalize vector %s'%self)
            self.u /= r
            self.v /= r

        def __str__(self):
            return "[ %6.3f %6.3f ]"%(self.u, self.v)

        def __mul__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = self.u * x
                v.v = self.v * x
                return v
            elif isinstance(x, NifFormat.TexCoord):
                return self.u * x.u + self.v * x.v
            else:
                raise TypeError("do not know how to multiply TexCoord with %s"%x.__class__)

        def __rmul__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = x * self.u
                v.v = x * self.v
                return v
            else:
                raise TypeError("do not know how to multiply %s and TexCoord"%x.__class__)

        def __add__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = self.u + x
                v.v = self.v + x
                return v
            elif isinstance(x, NifFormat.TexCoord):
                v = NifFormat.TexCoord()
                v.u = self.u + x.u
                v.v = self.v + x.v
                return v
            else:
                raise TypeError("do not know how to add TexCoord and %s"%x.__class__)

        def __radd__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = x + self.u
                v.v = x + self.v
                return v
            else:
                raise TypeError("do not know how to add %s and TexCoord"%x.__class__)

        def __sub__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = self.u - x
                v.v = self.v - x
                return v
            elif isinstance(x, NifFormat.TexCoord):
                v = NifFormat.TexCoord()
                v.u = self.u - x.u
                v.v = self.v - x.v
                return v
            else:
                raise TypeError("do not know how to substract TexCoord and %s"%x.__class__)

        def __rsub__(self, x):
            if isinstance(x, (float, int, long)):
                v = NifFormat.TexCoord()
                v.u = x - self.u
                v.v = x - self.v
                return v
            else:
                raise TypeError("do not know how to substract %s and TexCoord"%x.__class__)

        def __neg__(self):
            v = NifFormat.TexCoord()
            v.u = -self.u
            v.v = -self.v
            return v

    class NiPSysData:
        def _get_filtered_attribute_list(self, data=None):
            # simple hack to act as if we force num_vertices = 0
            for attr in StructBase._get_filtered_attribute_list(self, data):
                if data and (attr.name in ["vertices",
                                           "normals", "tangents", "bitangents",
                                           "vertex_colors", "uv_sets"]):
                    if data.version >= 0x14020007 and data.user_version == 11:
                        continue
                yield attr

if __name__=='__main__':
    import doctest
    doctest.testmod()
