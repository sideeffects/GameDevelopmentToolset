"""
:mod:`pyffi.spells.nif.fix` ---  spells to fix errors
=====================================================

Module which contains all spells that fix something in a nif.

Implementation
--------------

.. autoclass:: SpellDelTangentSpace
   :show-inheritance:
   :members:

.. autoclass:: SpellAddTangentSpace
   :show-inheritance:
   :members:

.. autoclass:: SpellFFVT3RSkinPartition
   :show-inheritance:
   :members:

.. autoclass:: SpellFixTexturePath
   :show-inheritance:
   :members:

.. autoclass:: SpellDetachHavokTriStripsData
   :show-inheritance:
   :members:

.. autoclass:: SpellClampMaterialAlpha
   :show-inheritance:
   :members:

.. autoclass:: SpellSendGeometriesToBindPosition
   :show-inheritance:
   :members:

.. autoclass:: SpellSendDetachedGeometriesToNodePosition
   :show-inheritance:
   :members:

.. autoclass:: SpellSendBonesToBindPosition
   :show-inheritance:
   :members:

.. autoclass:: SpellMergeSkeletonRoots
   :show-inheritance:
   :members:

.. autoclass:: SpellApplySkinDeformation
   :show-inheritance:
   :members:

.. autoclass:: SpellScale
   :show-inheritance:
   :members:

.. autoclass:: SpellFixCenterRadius
   :show-inheritance:
   :members:

.. autoclass:: SpellFixSkinCenterRadius
   :show-inheritance:
   :members:

.. autoclass:: SpellFixMopp
   :show-inheritance:
   :members:

.. autoclass:: SpellCleanStringPalette
   :show-inheritance:
   :members:

.. autoclass:: SpellDelUnusedRoots
   :show-inheritance:
   :members:

.. autoclass:: SpellFixEmptySkeletonRoots
   :show-inheritance:
   :members:

Regression tests
----------------
"""

# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------

from pyffi.formats.nif import NifFormat
from pyffi.spells.nif import NifSpell
import pyffi.spells.nif
import pyffi.spells.nif.check # recycle checking spells for update spells

class SpellDelTangentSpace(NifSpell):
    """Delete tangentspace if it is present."""

    SPELLNAME = "fix_deltangentspace"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiBinaryExtraData)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTriBasedGeom):
            # does this block have tangent space data?
            for extra in branch.get_extra_datas():
                if isinstance(extra, NifFormat.NiBinaryExtraData):
                    if (extra.name ==
                        'Tangent space (binormal & tangent vectors)'):
                        self.toaster.msg("removing tangent space block")
                        branch.remove_extra_data(extra)
                        self.changed = True
            # all extra blocks here done; no need to recurse further
            return False
        # recurse further
        return True

class SpellAddTangentSpace(NifSpell):
    """Add tangentspace if none is present."""

    SPELLNAME = "fix_addtangentspace"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiTriBasedGeom)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTriBasedGeom):
            # does this block have tangent space data?
            for extra in branch.get_extra_datas():
                if isinstance(extra, NifFormat.NiBinaryExtraData):
                    if (extra.name ==
                        'Tangent space (binormal & tangent vectors)'):
                        # tangent space found, done!
                        return False
            # no tangent space found
            self.toaster.msg("adding tangent space")
            branch.update_tangent_space()
            self.changed = True
            # all extra blocks here done; no need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellFFVT3RSkinPartition(NifSpell):
    """Create or update skin partition, with settings that work for Freedom
    Force vs. The 3rd Reich."""

    SPELLNAME = "fix_ffvt3rskinpartition"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiSkinInstance)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTriBasedGeom):
            # if the branch has skinning info
            if branch.skin_instance:
                # then update the skin partition
                self.toaster.msg("updating skin partition")
                branch.update_skin_partition(
                    maxbonesperpartition=4, maxbonespervertex=4,
                    stripify=False, verbose=0, padbones=True)
                self.changed = True
            return False
            # done; no need to recurse further in this branch
        else:
            # recurse further
            return True

class SpellParseTexturePath(NifSpell):
    """Base class for spells which must parse all texture paths, with
    hook for texture path substitution.
    """

    # abstract spell, so no spell name
    READONLY = False

    def substitute(self, old_path):
        """Helper function to allow subclasses of this spell to
        change part of the path with minimum of code.
        This implementation returns path unmodified.
        """
        return old_path

    def datainspect(self):
        # only run the spell if there are NiSourceTexture blocks
        return self.inspectblocktype(NifFormat.NiSourceTexture)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch, texturing properties and source
        # textures
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTexturingProperty,
                                   NifFormat.NiSourceTexture))
    
    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSourceTexture):
            branch.file_name = self.substitute(branch.file_name)
            return False
        else:
            return True

class SpellFixTexturePath(SpellParseTexturePath):
    r"""Fix the texture path. Transforms 0x0a into \n and 0x0d into
    \r. This fixes a bug in nifs saved with older versions of
    nifskope. Also transforms / into \. This fixes problems when
    packing files into a bsa archive. Also if the version is 20.0.0.4
    or higher it will check for bad texture path form of e.g.
    c:\program files\bethsoft\ob\textures\file\path.dds and replace it
    with e.g. textures\file\path.dds.
    """

    SPELLNAME = "fix_texturepath"
	
    def substitute(self, old_path):
        new_path = old_path
        new_path = new_path.replace(
            '\n'.encode("ascii"),
            '\\n'.encode("ascii"))
        new_path = new_path.replace(
            '\r'.encode("ascii"),
            '\\r'.encode("ascii"))
        new_path = new_path.replace(
            '/'.encode("ascii"),
            '\\'.encode("ascii"))
        # baphometal found some nifs that use double slashes
        # this causes textures not to show, so here we convert them
        # back to single slashes
        new_path = new_path.replace(
            '\\\\'.encode("ascii"),
            '\\'.encode("ascii"))
        textures_index = new_path.lower().find("textures\\")
        if textures_index > 0:
            # path contains textures\ at position other than starting
            # position
            new_path = new_path[textures_index:]
        if new_path != old_path:
            self.toaster.msg("fixed file name '%s'" % new_path)
            self.changed = True
        return new_path

# the next spell solves issue #2065018, MiddleWolfRug01.NIF
class SpellDetachHavokTriStripsData(NifSpell):
    """For NiTriStrips if their NiTriStripsData also occurs in a
    bhkNiTriStripsShape, make deep copy of data in havok. This is
    mainly useful as a preperation for other spells that act on
    NiTriStripsData, to ensure that the havok data remains untouched."""

    SPELLNAME = "fix_detachhavoktristripsdata"
    READONLY = False

    def __init__(self, *args, **kwargs):
        NifSpell.__init__(self, *args, **kwargs)
        # provides the bhknitristripsshapes within the current NiTriStrips
        self.bhknitristripsshapes = None

    def datainspect(self):
        # only run the spell if there are bhkNiTriStripsShape blocks
        return self.inspectblocktype(NifFormat.bhkNiTriStripsShape)

    def dataentry(self):
        # build list of all NiTriStrips blocks
        self.nitristrips = [branch for branch in self.data.get_global_iterator()
                            if isinstance(branch, NifFormat.NiTriStrips)]
        if self.nitristrips:
            return True
        else:
            return False

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch and collision branch
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRefObject))
    
    def branchentry(self, branch):
        if isinstance(branch, NifFormat.bhkNiTriStripsShape):
            for i, data in enumerate(branch.strips_data):
                if data in [otherbranch.data
                            for otherbranch in self.nitristrips]:
                        # detach!
                        self.toaster.msg("detaching havok data")
                        branch.strips_data[i] = NifFormat.NiTriStripsData().deepcopy(data)
                        self.changed = True
            return False
        else:
            return True

class SpellClampMaterialAlpha(NifSpell):
    """Clamp corrupted material alpha values."""

    SPELLNAME = "fix_clampmaterialalpha"
    READONLY = False

    def datainspect(self):
        # only run the spell if there are material property blocks
        return self.inspectblocktype(NifFormat.NiMaterialProperty)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch, and material properties
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiMaterialProperty))
    
    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiMaterialProperty):
            # check if alpha exceeds usual values
            if branch.alpha > 1:
                # too large
                self.toaster.msg(
                    "clamping alpha value (%f -> 1.0)" % branch.alpha)
                branch.alpha = 1.0
                self.changed = True
            elif branch.alpha < 0:
                # too small
                self.toaster.msg(
                    "clamping alpha value (%f -> 0.0)" % branch.alpha)
                branch.alpha = 0.0
                self.changed = True
            # stop recursion
            return False
        else:
            # keep recursing into children
            return True

class SpellSendGeometriesToBindPosition(pyffi.spells.nif.SpellVisitSkeletonRoots):
    """Transform skinned geometries so similar bones have the same bone data,
    and hence, the same bind position, over all geometries.
    """
    SPELLNAME = "fix_sendgeometriestobindposition"
    READONLY = False

    def skelrootentry(self, branch):
        self.toaster.msg("sending geometries to bind position")
        branch.send_geometries_to_bind_position()
        self.changed = True

class SpellSendDetachedGeometriesToNodePosition(pyffi.spells.nif.SpellVisitSkeletonRoots):
    """Transform geometries so each set of geometries that shares bones
    is aligned with the transform of the root bone of that set.
    """
    SPELLNAME = "fix_senddetachedgeometriestonodeposition"
    READONLY = False

    def skelrootentry(self, branch):
        self.toaster.msg("sending detached geometries to node position")
        branch.send_detached_geometries_to_node_position()
        self.changed = True

class SpellSendBonesToBindPosition(pyffi.spells.nif.SpellVisitSkeletonRoots):
    """Transform bones so bone data agrees with bone transforms,
    and hence, all bones are in bind position.
    """
    SPELLNAME = "fix_sendbonestobindposition"
    READONLY = False

    def skelrootentry(self, branch):
        self.toaster.msg("sending bones to bind position")
        branch.send_bones_to_bind_position()
        self.changed = True

class SpellMergeSkeletonRoots(NifSpell):
    """Merges skeleton roots in the nif file so that no skeleton root has
    another skeleton root as child. Warns if merge is impossible (this happens
    if the global skin data of the geometry is not the unit transform).
    """
    SPELLNAME = "fix_mergeskeletonroots"
    READONLY = False

    def datainspect(self):
        # only run the spell if there are skinned geometries
        return self.inspectblocktype(NifFormat.NiSkinInstance)

    def dataentry(self):
        # make list of skeleton roots
        skelroots = []
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiGeometry):
                if branch.skin_instance:
                    skelroot = branch.skin_instance.skeleton_root
                    if skelroot and not skelroot in skelroots:
                        skelroots.append(skelroot)
        # find the 'root' skeleton roots (those that have no other skeleton
        # roots as child)
        self.skelrootlist = set()
        for skelroot in skelroots:
            for skelroot_other in skelroots:
                if skelroot_other is skelroot:
                    continue
                if skelroot_other.find_chain(skelroot):
                    # skelroot_other has skelroot as child
                    # so skelroot is no longer an option
                    break
            else:
                # no skeleton root children!
                self.skelrootlist.add(skelroot)
        # only apply spell if there are skeleton roots
        if self.skelrootlist:
            return True
        else:
            return False

    def branchinspect(self, branch):
        # only inspect the NiNode branch
        return isinstance(branch, NifFormat.NiNode)
    
    def branchentry(self, branch):
        if branch in self.skelrootlist:
            result, failed = branch.merge_skeleton_roots()
            self.changed = True
            for geom in result:
                self.toaster.msg("reassigned skeleton root of %s" % geom.name)
            self.skelrootlist.remove(branch)
        # continue recursion only if there is still more to come
        if self.skelrootlist:
            return True
        else:
            return False

class SpellApplySkinDeformation(NifSpell):
    """Apply skin deformation to nif."""
    # TODO
    pass

class SpellScale(NifSpell):
    """Scale a model."""

    SPELLNAME = "fix_scale"
    READONLY = False

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify scale as argument (e.g. -a 10) "
                "to apply spell")
            return False
        else:
            toaster.scale = float(toaster.options["arg"])
            return True

    def dataentry(self):
        # initialize list of blocks that have been scaled
        self.toaster.msg("scaling by factor %f" % self.toaster.scale)
        self.scaled_branches = []
        return True

    def branchinspect(self, branch):
        # only do every branch once
        return (branch not in self.scaled_branches)

    def branchentry(self, branch):
        branch.apply_scale(self.toaster.scale)
        self.changed = True
        self.scaled_branches.append(branch)
        # continue recursion
        return True

class SpellFixCenterRadius(pyffi.spells.nif.check.SpellCheckCenterRadius):
    """Recalculate geometry centers and radii."""
    SPELLNAME = "fix_centerradius"
    READONLY = False

class SpellFixSkinCenterRadius(pyffi.spells.nif.check.SpellCheckSkinCenterRadius):
    """Recalculate skin centers and radii."""
    SPELLNAME = "fix_skincenterradius"
    READONLY = False

class SpellFixMopp(pyffi.spells.nif.check.SpellCheckMopp):
    """Recalculate mopp data from collision geometry."""
    SPELLNAME = "fix_mopp"
    READONLY = False

    def branchentry(self, branch):
        # we don't recycle the check mopp code here
        # that spell does not actually recalculate the mopp at all
        # it only parses the existing mopp...
        if not isinstance(branch, NifFormat.bhkMoppBvTreeShape):
            # keep recursing
            return True
        else:
            self.toaster.msg("updating mopp")
            branch.update_mopp()
            self.changed = True

class SpellCleanStringPalette(NifSpell):
    """Remove unused strings from string palette."""

    SPELLNAME = "fix_cleanstringpalette"
    READONLY = False

    def substitute(self, old_string):
        """Helper function to substitute strings in the string palette,
        to allow subclasses of this spell can modify the strings.
        This implementation returns string unmodified.
        """
        return old_string

    def datainspect(self):
        # only run the spell if there is a string palette block
        return self.inspectblocktype(NifFormat.NiStringPalette)

    def branchinspect(self, branch):
        # only inspect branches where NiControllerSequence can occur
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiControllerManager,
                                   NifFormat.NiControllerSequence))

    def branchentry(self, branch):
        """Parses string palette of either a single controller sequence,
        or of all controller sequences in a controller manager.

        >>> seq = NifFormat.NiControllerSequence()
        >>> seq.string_palette = NifFormat.NiStringPalette()
        >>> block = seq.add_controlled_block()
        >>> block.string_palette = seq.string_palette
        >>> block.set_variable_1("there")
        >>> block.set_node_name("hello")
        >>> block.string_palette.palette.add_string("test")
        12
        >>> seq.string_palette.palette.get_all_strings()
        ['there', 'hello', 'test']
        >>> SpellCleanStringPalette().branchentry(seq)
        pyffi.toaster:INFO:parsing string palette
        False
        >>> seq.string_palette.palette.get_all_strings()
        ['hello', 'there']
        >>> block.get_variable_1()
        'there'
        >>> block.get_node_name()
        'hello'
        """
        if isinstance(branch, (NifFormat.NiControllerManager,
                               NifFormat.NiControllerSequence)):
            # get list of controller sequences
            if isinstance(branch, NifFormat.NiControllerManager):
                # multiple controller sequences sharing a single
                # string palette
                if not branch.controller_sequences:
                    # no controller sequences: nothing to do
                    return False
                controller_sequences = branch.controller_sequences
            else:
                # unmanaged controller sequence
                controller_sequences = [branch]
            # and clean their string palettes
            self.toaster.msg("parsing string palette")
            # use the first string palette as reference
            string_palette = controller_sequences[0].string_palette
            palette = string_palette.palette
            # 1) calculate number of strings, for reporting
            #    (this assumes that all blocks already use the same
            #    string palette!)
            num_strings = len(palette.get_all_strings())
            # 2) substitute strings
            # first convert the controlled block strings to the old style
            # (storing the actual string, and not just an offset into the
            # string palette)
            for controller_sequence in controller_sequences:
                for block in controller_sequence.controlled_blocks:
                    # set old style strings from string palette strings
                    block.node_name = self.substitute(block.get_node_name())
                    block.property_type = self.substitute(block.get_property_type())
                    block.controller_type = self.substitute(block.get_controller_type())
                    block.variable_1 = self.substitute(block.get_variable_1())
                    block.variable_2 = self.substitute(block.get_variable_2())
                    # ensure single string palette for all controlled blocks
                    block.string_palette = string_palette
                # ensure single string palette for all controller sequences
                controller_sequence.string_palette = string_palette
            # clear the palette
            palette.clear()
            # and then convert old style back to new style
            for controller_sequence in controller_sequences:
                for block in controller_sequence.controlled_blocks:
                    block.set_node_name(block.node_name)
                    block.set_property_type(block.property_type)
                    block.set_controller_type(block.controller_type)
                    block.set_variable_1(block.variable_1)
                    block.set_variable_2(block.variable_2)
            self.changed = True
            # do not recurse further
            return False
        else:
            # keep looking for managers or sequences
            return True

class SpellDelUnusedRoots(pyffi.spells.nif.NifSpell):
    """Remove root branches that shouldn't be root branches and are
    unused in the file such as NiProperty branches that are not
    properly parented.
    """

    SPELLNAME = "fix_delunusedroots"
    READONLY = False

    def datainspect(self):
        if self.inspectblocktype(NifFormat.NiAVObject):
            # check last 8 bytes
            pos = self.stream.tell()
            try:
                self.stream.seek(-8, 2)
                if self.stream.read(8) == '\x01\x00\x00\x00\x00\x00\x00\x00':
                    # standard nif with single root: do not remove anything
                    # and quit early without reading the full file
                    return False
                else:
                    return True
            finally:
                self.stream.seek(pos)
        else:
            return False

    def dataentry(self):
        # make list of good roots
        good_roots = [
            root for root in self.data.roots
            if isinstance(root, (NifFormat.NiAVObject,
                                 NifFormat.NiSequence,
                                 NifFormat.NiPixelData,
                                 NifFormat.NiPhysXProp,
                                 NifFormat.NiSequenceStreamHelper))]
        # if actual roots differ from good roots set roots to good
        # roots and report
        if self.data.roots != good_roots:
            self.toaster.msg("removing %i bad roots"
                             % (len(self.data.roots) - len(good_roots)))
            self.data.roots = good_roots
            self.changed = True
        return False

class SpellFixBhkSubShapes(NifSpell):
    """Fix bad subshape vertex counts in bhkPackedNiTriStripsShape blocks."""

    SPELLNAME = "fix_bhksubshapes"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.bhkPackedNiTriStripsShape)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch and collision branch
        return isinstance(branch, (
            NifFormat.NiAVObject,
            NifFormat.bhkCollisionObject,
            NifFormat.bhkRefObject))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.bhkPackedNiTriStripsShape):
            if not branch.data:
                # no data... this is weird, but let's just ignore it
                return False
            # calculate number of vertices in subshapes
            num_verts_in_sub_shapes = sum(
                (sub_shape.num_vertices
                 for sub_shape in branch.get_sub_shapes()), 0)
            if num_verts_in_sub_shapes != branch.data.num_vertices:
                self.toaster.logger.warn(
                    "bad subshape vertex count (expected %i, got %i)"
                    % (branch.data.num_vertices, num_verts_in_sub_shapes))
                # remove or add vertices from subshapes (start with the last)
                for sub_shape in reversed(branch.get_sub_shapes()):
                    self.toaster.msg("fixing count in subshape")
                    # calculate new number of vertices
                    # if everything were to be fixed with this shape
                    sub_shape_num_vertices = (
                        sub_shape.num_vertices
                        + branch.data.num_vertices
                        - num_verts_in_sub_shapes)
                    if sub_shape_num_vertices > 0:
                        # we can do everything in the last shape
                        # so do it
                        sub_shape.num_vertices = sub_shape_num_vertices
                        break
                    else:
                        # too many to remove...
                        # first remove everything from this shape
                        # the remainder will come from the following shapes
                        num_verts_in_sub_shapes -= sub_shape.num_vertices
                        sub_shape.num_vertices = 0
            # no need to recurse further
            return False
        # recurse further
        return True

class SpellFixEmptySkeletonRoots(NifSpell):
    """Fix empty skeleton roots in an as sane as possible way."""

    SPELLNAME = "fix_emptyskeletonroots"
    READONLY = False

    def datainspect(self):
        # only run the spell if there is a skin instance block
        return self.inspectblocktype(NifFormat.NiSkinInstance)

    def dataentry(self):
        # set skeleton root: first block of data
        # this is what the engine usually seems to assume if it is not present
        if not self.data.roots:
            return False
        self.skeleton_root = self.data.roots[0]
        # sanity check
        if not isinstance(self.skeleton_root, NifFormat.NiAVObject):
            # we'll fail in this case...
            self.skeleton_root = None
            self.toaster.logger.info("no skeleton root candidate")
            return False
        return True

    def branchinspect(self, branch):
        # only inspect branches where NiSkinInstance can occur
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiSkinInstance))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSkinInstance):
            if not branch.skeleton_root:
                if self.skeleton_root:
                    self.toaster.logger.warn(
                        "fixed missing skeleton root")
                    branch.skeleton_root = self.skeleton_root
                    self.changed = True
                else:
                    self.toaster.logger.error(
                        "missing skeleton root, "
                        "but no skeleton root candidate!")
            # do not recurse further
            return False
        else:
            # keep looking for managers or sequences
            return True
