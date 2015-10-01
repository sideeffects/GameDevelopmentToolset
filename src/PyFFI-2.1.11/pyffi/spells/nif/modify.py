"""
:mod:`pyffi.spells.nif.modify` ---  spells to make modifications
=================================================================
Module which contains all spells that modify a nif.

.. autoclass:: SpellTexturePath
   :show-inheritance:
   :members:

.. autoclass:: SpellSubstituteTexturePath
   :show-inheritance:
   :members:

.. autoclass:: SpellLowResTexturePath
   :show-inheritance:
   :members:

.. autoclass:: SpellCollisionType
   :show-inheritance:
   :members:

.. autoclass:: SpellCollisionMaterial
   :show-inheritance:
   :members:

.. autoclass:: SpellScaleAnimationTime
   :show-inheritance:
   :members:

.. autoclass:: SpellReverseAnimation
   :show-inheritance:
   :members:

.. autoclass:: SpellSubstituteStringPalette
   :show-inheritance:
   :members:

.. autoclass:: SpellChangeBonePriorities
   :show-inheritance:
   :members:

.. autoclass:: SpellSetInterpolatorTransRotScale
   :show-inheritance:
   :members:

.. autoclass:: SpellDelInterpolatorTransformData
   :show-inheritance:
   :members:

.. autoclass:: SpellDelBranches
   :show-inheritance:
   :members:

.. autoclass:: _SpellDelBranchClasses
   :show-inheritance:
   :members:

.. autoclass:: SpellDelSkinShapes
   :show-inheritance:
   :members:

.. autoclass:: SpellDisableParallax
   :show-inheritance:
   :members:

.. autoclass:: SpellAddStencilProperty
   :show-inheritance:
   :members:

.. autoclass:: SpellDelVertexColor
   :show-inheritance:
   :members:

.. autoclass:: SpellMakeSkinlessNif
   :show-inheritance:
   :members:

.. autoclass:: SpellCleanFarNif
   :show-inheritance:
   :members:

.. autoclass:: SpellMakeFarNif
   :show-inheritance:
   :members:

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
from pyffi.object_models.common import _as_bytes
from pyffi.spells.nif import NifSpell
import pyffi.spells.nif
import pyffi.spells.nif.check # recycle checking spells for update spells
import pyffi.spells.nif.fix

from itertools import izip
import os
import re # for modify_substitutestringpalette and modify_substitutetexturepath

class SpellTexturePath(
    pyffi.spells.nif.fix.SpellParseTexturePath):
    """Changes the texture path while keeping the texture names."""

    SPELLNAME = "modify_texturepath"
    READONLY = False

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify path as argument "
                "(e.g. -a textures\\pm\\dungeons\\bloodyayleid\\interior) "
                "to apply spell")
            return False
        else:
            toaster.texture_path = str(toaster.options["arg"])
            # standardize the path
            toaster.texture_path = toaster.texture_path.replace("/", os.sep)
            toaster.texture_path = toaster.texture_path.replace("\\", os.sep)
            return True

    def substitute(self, old_path):
        # note: replace backslashes by os.sep in filename, and
        # when joined, revert them back, for linux
        new_path = os.path.join(
            self.toaster.texture_path,
            os.path.basename(old_path.replace("\\", os.sep))
            ).replace(os.sep, "\\")
        if new_path != old_path:
            self.changed = True
            self.toaster.msg("%s -> %s" % (old_path, new_path))
        return new_path

class SpellSubstituteTexturePath(
    pyffi.spells.nif.fix.SpellFixTexturePath):
    """Runs a regex replacement on texture paths."""

    SPELLNAME = "modify_substitutetexturepath"

    @classmethod
    def toastentry(cls, toaster):
        arg = toaster.options["arg"]
        if not arg:
            # missing arg
            toaster.logger.warn(
                "must specify regular expression and substitution as argument "
                "(e.g. -a /architecture/city) to apply spell")
            return False
        dummy, toaster.regex, toaster.sub = arg.split(arg[0])
        toaster.sub = _as_bytes(toaster.sub)
        toaster.regex = re.compile(_as_bytes(toaster.regex))
        return True    

    def substitute(self, old_path):
        """Returns modified texture path, and reports if path was modified.
        """
        if not old_path:
            # leave empty path be
            return old_path
        new_path = self.toaster.regex.sub(self.toaster.sub, old_path)
        if old_path != new_path:
            self.changed = True
            self.toaster.msg("%s -> %s" % (old_path, new_path))
        return new_path

class SpellLowResTexturePath(SpellSubstituteTexturePath):
    """Changes the texture path by replacing 'textures\\*' with 
    'textures\\lowres\\*' - used mainly for making _far.nifs
    """

    SPELLNAME = "modify_texturepathlowres"

    @classmethod
    def toastentry(cls, toaster):
        toaster.sub = _as_bytes("textures\\\\lowres\\\\")
        toaster.regex = re.compile(_as_bytes("^textures\\\\"), re.IGNORECASE)
        return True

    def substitute(self, old_path):
        if (_as_bytes('\\lowres\\') not in old_path.lower()):
            return SpellSubstituteTexturePath.substitute(self, old_path)
        else:
            return old_path

class SpellCollisionType(NifSpell):
    """Sets the object collision to be a different type"""

    SPELLNAME = "modify_collisiontype"
    READONLY = False

    class CollisionTypeStatic:
        layer = 1
        motion_system = 7
        unknown_byte1 = 1
        unknown_byte2 = 1
        quality_type = 1
        wind = 0
        solid = True
        mass = 0

    class CollisionTypeAnimStatic(CollisionTypeStatic):
        layer = 2
        motion_system = 6
        unknown_byte1 = 2
        unknown_byte2 = 2
        quality_type = 2

    class CollisionTypeTerrain(CollisionTypeStatic):
        layer = 14
        motion_system = 7

    class CollisionTypeClutter(CollisionTypeAnimStatic):
        layer = 4
        motion_system = 4
        quality_type = 3
        mass = 10

    class CollisionTypeWeapon(CollisionTypeClutter):
        layer = 5
        mass = 25
		
    class CollisionTypeNonCollidable(CollisionTypeStatic):
        layer = 15
        motion_system = 7

    COLLISION_TYPE_DICT = {
        "static": CollisionTypeStatic,
        "anim_static": CollisionTypeAnimStatic,
        "clutter": CollisionTypeClutter,
        "weapon": CollisionTypeWeapon,
        "terrain": CollisionTypeTerrain,
        "non_collidable": CollisionTypeNonCollidable
        }

    @classmethod
    def toastentry(cls, toaster):
        try:
            toaster.col_type = cls.COLLISION_TYPE_DICT[toaster.options["arg"]]
        except KeyError:
            # incorrect arg
            toaster.logger.warn(
                "must specify collision type to change to as argument "
                "(e.g. -a static (accepted names: %s) "
                "to apply spell"
                % ", ".join(cls.COLLISION_TYPE_DICT.iterkeys()))
            return False
        else:
            return True

    def datainspect(self):
        return self.inspectblocktype(NifFormat.bhkRigidBody)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRigidBody,
                                   NifFormat.bhkMoppBvTreeShape,
                                   NifFormat.bhkPackedNiTriStripsShape))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.bhkRigidBody):
            self.changed = True
            branch.layer = self.toaster.col_type.layer
            branch.layer_copy = self.toaster.col_type.layer
            branch.mass = self.toaster.col_type.mass
            branch.motion_system = self.toaster.col_type.motion_system
            branch.unknown_byte_1 = self.toaster.col_type.unknown_byte1
            branch.unknown_byte_2 = self.toaster.col_type.unknown_byte2
            branch.quality_type = self.toaster.col_type.quality_type
            branch.wind = self.toaster.col_type.wind
            branch.solid = self.toaster.col_type.solid
            self.toaster.msg("collision set to %s"
                             % self.toaster.options["arg"])
            # bhkPackedNiTriStripsShape could be further down, so keep looking
            return True
        elif isinstance(branch, NifFormat.bhkPackedNiTriStripsShape):
            self.changed = True
            for subshape in branch.get_sub_shapes():
                subshape.layer = self.toaster.col_type.layer
            self.toaster.msg("collision set to %s"
                             % self.toaster.options["arg"])
            # all extra blocks here done; no need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellScaleAnimationTime(NifSpell):
    """Scales the animation time."""

    SPELLNAME = "modify_scaleanimationtime"
    READONLY = False
    
    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify scaling number as argument "
                "(e.g. -a 0.6) to apply spell")
            return False
        else:
            toaster.animation_scale = float(toaster.options["arg"])
            return True

    def datainspect(self):
        # returns more than needed but easiest way to ensure it catches all
        # types of animations
        return True

    def branchinspect(self, branch):
        # inspect the NiAVObject branch, and NiControllerSequence
        # branch (for kf files)
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTimeController,
                                   NifFormat.NiInterpolator,
                                   NifFormat.NiControllerManager,
                                   NifFormat.NiControllerSequence,
                                   NifFormat.NiKeyframeData,
                                   NifFormat.NiTextKeyExtraData,
                                   NifFormat.NiFloatData))

    def branchentry(self, branch):

        def scale_key_times(keys):
            """Helper function to scale key times."""
            for key in keys:
                key.time *= self.toaster.animation_scale

        if isinstance(branch, NifFormat.NiKeyframeData):
            self.changed = True
            if branch.rotation_type == 4:
                scale_key_times(branch.xyz_rotations[0].keys)
                scale_key_times(branch.xyz_rotations[1].keys)
                scale_key_times(branch.xyz_rotations[2].keys)
            else:
                scale_key_times(branch.quaternion_keys)
            scale_key_times(branch.translations.keys)
            scale_key_times(branch.scales.keys)
            # no children of NiKeyframeData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiControllerSequence):
            self.changed = True
            branch.stop_time *= self.toaster.animation_scale
            # recurse further into children of NiControllerSequence
            return True
        elif isinstance(branch, NifFormat.NiTextKeyExtraData):
            self.changed = True
            scale_key_times(branch.text_keys)
            # no children of NiTextKeyExtraData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiTimeController):
            self.changed = True
            branch.stop_time *= self.toaster.animation_scale
            # recurse further into children of NiTimeController
            return True
        elif isinstance(branch, NifFormat.NiFloatData):
            self.changed = True
            scale_key_times(branch.data.keys)
            # no children of NiFloatData so no need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellReverseAnimation(NifSpell):
    """Reverses the animation by reversing datas in relation to the time."""

    SPELLNAME = "modify_reverseanimation"
    READONLY = False

    def datainspect(self):
        # returns more than needed but easiest way to ensure it catches all
        # types of animations
        return True

    def branchinspect(self, branch):
        # inspect the NiAVObject branch, and NiControllerSequence
        # branch (for kf files)
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTimeController,
                                   NifFormat.NiInterpolator,
                                   NifFormat.NiControllerManager,
                                   NifFormat.NiControllerSequence,
                                   NifFormat.NiKeyframeData,
                                   NifFormat.NiTextKeyExtraData,
                                   NifFormat.NiFloatData))

    def branchentry(self, branch):

        def reverse_keys(keys):
            """Helper function to reverse keys."""
            # copy the values
            key_values = [key.value for key in keys]
            # reverse them
            for key, new_value in izip(keys, reversed(key_values)):
                key.value = new_value

        if isinstance(branch, NifFormat.NiKeyframeData):
            self.changed = True
            # (this also covers NiTransformData)
            if branch.rotation_type == 4:
                reverse_keys(branch.xyz_rotations[0].keys)
                reverse_keys(branch.xyz_rotations[1].keys)
                reverse_keys(branch.xyz_rotations[2].keys)
            else:
                reverse_keys(branch.quaternion_keys)
            reverse_keys(branch.translations.keys)
            reverse_keys(branch.scales.keys)
            # no children of NiTransformData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiTextKeyExtraData):
            self.changed = True
            reverse_keys(branch.text_keys)
            # no children of NiTextKeyExtraData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiFloatData):
            self.changed = True
            reverse_keys(branch.data.keys)
            # no children of NiFloatData so no need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellCollisionMaterial(NifSpell):
    """Sets the object's collision material to be a different type"""

    SPELLNAME = "modify_collisionmaterial"
    READONLY = False

    class CollisionMaterialStone:
        material = 0

    class CollisionMaterialCloth:
        material = 1

    class CollisionMaterialMetal:
        material = 5

    COLLISION_MATERIAL_DICT = {
        "stone": CollisionMaterialStone,
        "cloth": CollisionMaterialCloth,
        "metal": CollisionMaterialMetal
        }

    @classmethod
    def toastentry(cls, toaster):
        try:
            toaster.col_material = cls.COLLISION_MATERIAL_DICT[toaster.options["arg"]]
        except KeyError:
            # incorrect arg
            toaster.logger.warn(
                "must specify collision material to change to as argument "
                "(e.g. -a stone (accepted names: %s) "
                "to apply spell"
                % ", ".join(cls.COLLISION_MATERIAL_DICT.iterkeys()))
            return False
        else:
            return True

    def datainspect(self):
        return self.inspectblocktype(NifFormat.bhkShape)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRigidBody,
                                   NifFormat.bhkShape))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.bhkShape):
            self.changed = True
            branch.material = self.toaster.col_material.material
            self.toaster.msg("collision material set to %s" % self.toaster.options["arg"])
            # bhkPackedNiTriStripsShape could be further down, so keep looking
            return True
        elif isinstance(branch, NifFormat.bhkPackedNiTriStripsShape):
            self.changed = True
            for subshape in branch.get_sub_shapes():
                subshape.material = self.toaster.col_type.material
            self.toaster.msg("collision material set to %s" % self.toaster.options["arg"])
            # all extra blocks here done; no need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellDelBranches(NifSpell):
    """Delete blocks that match the exclude list."""

    SPELLNAME = "modify_delbranches"
    READONLY = False

    def is_branch_to_be_deleted(self, branch):
        """Returns ``True`` for those branches that must be deleted.
        The default implementation returns ``True`` for branches that
        are not admissible as specified by include/exclude options of
        the toaster. Override in subclasses that must delete specific
        branches.
        """
        # check if it is excluded or not
        return not self.toaster.is_admissible_branch_class(branch.__class__)

    def _branchinspect(self, branch):
        """This spell inspects every branch, also the non-admissible ones,
        therefore we must override this method.
        """
        return True

    def branchentry(self, branch):
        """Strip branch if it is flagged for deletion.
        """
        # check if it is to be deleted or not
        if self.is_branch_to_be_deleted(branch):
            # it is, wipe it out
            self.toaster.msg("stripping this branch")
            self.data.replace_global_node(branch, None)
            self.changed = True
            # do not recurse further
            return False
        else:
            # this one was not excluded, keep recursing
            return True

class _SpellDelBranchClasses(SpellDelBranches):
    """Delete blocks that match a given list. Only useful as base class
    for other spells.
    """

    BRANCH_CLASSES_TO_BE_DELETED = ()
    """List of branch classes that have to be deleted."""

    def datainspect(self):
        return any(
            self.inspectblocktype(branch_class)
            for branch_class in self.BRANCH_CLASSES_TO_BE_DELETED)

    def is_branch_to_be_deleted(self, branch):
        return isinstance(branch, self.BRANCH_CLASSES_TO_BE_DELETED)

class SpellDelVertexColor(SpellDelBranches):
    """Delete vertex color properties and vertex color data."""

    SPELLNAME = "modify_delvertexcolor"

    def is_branch_to_be_deleted(self, branch):
        return isinstance(branch, NifFormat.NiVertexColorProperty)

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiTriBasedGeom)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTriBasedGeomData,
                                   NifFormat.NiVertexColorProperty))

    def branchentry(self, branch):
        # delete vertex color property
        SpellDelBranches.branchentry(self, branch)
        # reset vertex color flags
        if isinstance(branch, NifFormat.NiTriBasedGeomData):
            if branch.has_vertex_colors:
                self.toaster.msg("removing vertex colors")
                branch.has_vertex_colors = False
                self.changed = True
            # no children; no need to recurse further
            return False
        # recurse further
        return True

# identical to niftoaster.py modify_delbranches -x NiVertexColorProperty
# delete?
class SpellDelVertexColorProperty(_SpellDelBranchClasses):
    """Delete vertex color property if it is present."""

    SPELLNAME = "modify_delvertexcolorprop"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiVertexColorProperty,)

# identical to niftoaster.py modify_delbranches -x NiAlphaProperty
# delete?
class SpellDelAlphaProperty(_SpellDelBranchClasses):
    """Delete alpha property if it is present."""

    SPELLNAME = "modify_delalphaprop"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiAlphaProperty,)

# identical to niftoaster.py modify_delbranches -x NiSpecularProperty
# delete?
class SpellDelSpecularProperty(_SpellDelBranchClasses):
    """Delete specular property if it is present."""

    SPELLNAME = "modify_delspecularprop"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiSpecularProperty,)

# identical to niftoaster.py modify_delbranches -x BSXFlags
# delete?
class SpellDelBSXFlags(_SpellDelBranchClasses):
    """Delete BSXFlags if any are present."""

    SPELLNAME = "modify_delbsxflags"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.BSXFlags,)
		
# identical to niftoaster.py modify_delbranches -x NiStringExtraData
# delete?
class SpellDelStringExtraDatas(_SpellDelBranchClasses):
    """Delete NiSringExtraDatas if they are present."""

    SPELLNAME = "modify_delstringextradatas"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiStringExtraData,)

class SpellDelSkinShapes(SpellDelBranches):
    """Delete any geometries with a material name of 'skin'"""

    SPELLNAME = "modify_delskinshapes"

    def is_branch_to_be_deleted(self, branch):
        if isinstance(branch, NifFormat.NiTriBasedGeom):
            for prop in branch.get_properties():
                if isinstance(prop, NifFormat.NiMaterialProperty):
                    if prop.name.lower() == "skin":
                        # skin material, tag for deletion
                        return True
        # do not delete anything else
        return False

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

# identical to niftoaster.py modify_delbranches -x NiCollisionObject
# delete?
class SpellDelCollisionData(_SpellDelBranchClasses):
    """Deletes any Collision data present."""

    SPELLNAME = "modify_delcollision"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiCollisionObject,)

# identical to niftoaster.py modify_delbranches -x NiTimeController
# delete?
class SpellDelAnimation(_SpellDelBranchClasses):
    """Deletes any animation data present."""

    SPELLNAME = "modify_delanimation"
    BRANCH_CLASSES_TO_BE_DELETED = (NifFormat.NiTimeController,)

class SpellDisableParallax(NifSpell):
    """Disable parallax shader (for Oblivion, but may work on other nifs too).
    """

    SPELLNAME = "modify_disableparallax"
    READONLY = False

    def datainspect(self):
        # XXX should we check that the nif is Oblivion version?
        # only run the spell if there are textures
        return self.inspectblocktype(NifFormat.NiTexturingProperty)

    def branchinspect(self, branch):
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTexturingProperty))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTexturingProperty):
            # is parallax enabled?
            if branch.apply_mode == 4:
                # yes!
                self.toaster.msg("disabling parallax shader")
                branch.apply_mode = 2
                self.changed = True
            # stop recursing
            return False
        else:
            # keep recursing
            return True

class SpellAddStencilProperty(NifSpell):
    """Adds a NiStencilProperty to each geometry if it is not present."""

    SPELLNAME = "modify_addstencilprop"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiTriBasedGeom)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTriBasedGeom):
            # does this block have an stencil property?
            for prop in branch.get_properties():
                if isinstance(prop, NifFormat.NiStencilProperty):
                    return False
            # no stencil property found
            self.toaster.msg("adding NiStencilProperty")
            branch.add_property(NifFormat.NiStencilProperty())
            self.changed = True
            # no geometry children, no need to recurse further
            return False
        # recurse further
        return True

# note: this should go into the optimize module
# but we have to put it here to avoid circular dependencies
class SpellCleanFarNif(
    pyffi.spells.SpellGroupParallel(
        SpellDelVertexColorProperty,
        SpellDelAlphaProperty,
        SpellDelSpecularProperty,
        SpellDelBSXFlags,
        SpellDelStringExtraDatas,
        pyffi.spells.nif.fix.SpellDelTangentSpace,
        SpellDelCollisionData,
        SpellDelAnimation,
        SpellDisableParallax)):
    """Spell to clean _far type nifs (for even more optimizations,
    combine this with the optimize spell).
    """

    SPELLNAME = "modify_cleanfarnif"

    # only apply spell on _far files
    def datainspect(self):
        return self.stream.name.endswith('_far.nif')

# TODO: implement via modify_delbranches?
# this is like SpellCleanFarNif but with changing the texture path
# and optimizing the geometry
class SpellMakeFarNif(
    pyffi.spells.SpellGroupParallel(
        SpellDelVertexColorProperty,
        SpellDelAlphaProperty,
        SpellDelSpecularProperty,
        SpellDelBSXFlags,
        SpellDelStringExtraDatas,
        pyffi.spells.nif.fix.SpellDelTangentSpace,
        SpellDelCollisionData,
        SpellDelAnimation,
        SpellDisableParallax,
        SpellLowResTexturePath)):
        #TODO: implement vert decreaser.
    """Spell to make _far type nifs (for even more optimizations,
    combine this with the optimize spell).
    """
    SPELLNAME = "modify_makefarnif"

class SpellMakeSkinlessNif(
    pyffi.spells.SpellGroupSeries(
        pyffi.spells.SpellGroupParallel(
            SpellDelSkinShapes,
            SpellAddStencilProperty)
        )):
    """Spell to make fleshless CMR (Custom Model Races) 
       clothing/armour type nifs.
    """
    SPELLNAME = "modify_makeskinlessnif"

class SpellSubstituteStringPalette(
    pyffi.spells.nif.fix.SpellCleanStringPalette):
    """Substitute strings in a string palette."""

    SPELLNAME = "modify_substitutestringpalette"

    @classmethod
    def toastentry(cls, toaster):
        arg = toaster.options["arg"]
        if not arg:
            # missing arg
            toaster.logger.warn(
                "must specify regular expression and substitution as argument "
                "(e.g. -a /Bip01/Bip02) to apply spell")
            return False
        dummy, toaster.regex, toaster.sub = arg.split(arg[0])
        toaster.sub = _as_bytes(toaster.sub)
        toaster.regex = re.compile(_as_bytes(toaster.regex))
        return True    

    def substitute(self, old_string):
        """Returns modified string, and reports if string was modified.
        """
        if not old_string:
            # leave empty strings be
            return old_string
        new_string = self.toaster.regex.sub(self.toaster.sub, old_string)
        if old_string != new_string:
            self.changed = True
            self.toaster.msg("%s -> %s" % (old_string, new_string))
        return new_string

class SpellChangeBonePriorities(NifSpell):
    """Changes controlled block priorities based on controlled block name."""

    SPELLNAME = "modify_bonepriorities"
    READONLY = False

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify bone(s) and priority(ies) as argument "
                "(e.g. -a 'bip01:50|bip01 spine:10') to apply spell "
                "make sure all bone names in lowercase")
            return False
        else:
            toaster.bone_priorities = dict(
                (name.lower(), int(priority))
                for (name, priority) in (
                    namepriority.split(":")
                    for namepriority in toaster.options["arg"].split("|")))
            return True

    def datainspect(self):
        # returns only if nif/kf contains NiSequence
        return self.inspectblocktype(NifFormat.NiSequence)
        
    def branchinspect(self, branch):
        # inspect the NiAVObject and NiSequence branches
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiControllerManager,
                                   NifFormat.NiSequence))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSequence):
            for controlled_block in branch.controlled_blocks:
                try:
                    controlled_block.priority = self.toaster.bone_priorities[
                        controlled_block.get_node_name().lower()]
                except KeyError:
                    # node name not in bone priority list
                    continue
                self.changed = True
                self.toaster.msg("%s priority changed to %d" %
                                 (controlled_block.get_node_name(),
                                  controlled_block.priority))
        return True

class SpellChangeAllBonePriorities(SpellChangeBonePriorities):
    """Changes all controlled block priorities to supplied argument."""

    SPELLNAME = "modify_allbonepriorities"

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify priority as argument (e.g. -a 20)")
            return False
        else:
            toaster.bone_priority = int(toaster.options["arg"])
            return True

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSequence):
            for controlled_block in branch.controlled_blocks:
                if controlled_block.priority == self.toaster.bone_priority:
                    self.toaster.msg("%s priority is already %d" %
                                     (controlled_block.get_node_name(),
                                      controlled_block.priority))
                else:
                    controlled_block.priority = self.toaster.bone_priority
                    self.changed = True
                    self.toaster.msg("%s priority changed to %d" %
                                     (controlled_block.get_node_name(),
                                      controlled_block.priority))
        return True

class SpellSetInterpolatorTransRotScale(NifSpell):
    """Changes specified bone(s) translations/rotations in their
    NiTransformInterpolator.
    """

    SPELLNAME = "modify_interpolatortransrotscale"
    READONLY = False

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify bone(s), translation and rotation for each"
                " bone as argument (e.g."
                " -a 'bip01:1,2,3;0,0,0,1;1|bip01 spine2:0,0,0;1,0,0,0.5;1')"
                " to apply spell; make sure all bone names are lowercase,"
                " first three numbers being translation,"
                " next three being rotation,"
                " last being scale;"
                " enter X to leave existing value for that value")
            return False
        else:
            def _float(x):
                if x == "X":
                    return None
                else:
                    return float(x)
                    
            toaster.interp_transforms = dict(
                (name.lower(), ([_float(x) for x in trans.split(",")],
                                [_float(x) for x in rot.split(",")],
                                _float(scale)))
                for (name, (trans, rot, scale)) in (
                    (name, transrotscale.split(";"))
                    for (name, transrotscale) in (
                        name_transrotscale.split(":")
                        for name_transrotscale
                        in toaster.options["arg"].split("|"))))
            return True

    def datainspect(self):
        # returns only if nif/kf contains NiSequence
        return self.inspectblocktype(NifFormat.NiSequence)
        
    def branchinspect(self, branch):
        # inspect the NiAVObject and NiSequence branches
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiSequence))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSequence):
            for controlled_block in branch.controlled_blocks:
                try:
                    (transx, transy, transz), (quatx, quaty, quatz, quatw), scale = self.toaster.interp_transforms[controlled_block.get_node_name().lower()]
                except KeyError:
                    # node name not in change list
                    continue
                interp = controlled_block.interpolator
                if transx is not None:
                    interp.translation.x = transx
                if transy is not None:
                    interp.translation.y = transy
                if transz is not None:
                    interp.translation.z = transz
                if quatx is not None:
                    interp.rotation.x = quatx
                if quaty is not None:
                    interp.rotation.y = quaty
                if quatz is not None:
                    interp.rotation.z = quatz
                if quatw is not None:
                    interp.rotation.w = quatw
                if scale is not None:
                    interp.scale = scale
                self.changed = True
                self.toaster.msg(
                    "%s rotated/translated/scaled as per argument"
                    % (controlled_block.get_node_name()))
        return True

class SpellDelInterpolatorTransformData(NifSpell):
    """Deletes the specified bone(s) NiTransformData(s)."""

    SPELLNAME = "modify_delinterpolatortransformdata"
    READONLY = False

    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify bone name(s) as argument "
                "(e.g. -a 'bip01|bip01 pelvis') to apply spell "
                "make sure all bone name(s) in lowercase")
            return False
        else:
            toaster.change_blocks = toaster.options["arg"].split('|')
            return True

    def datainspect(self):
        # returns only if nif/kf contains NiSequence
        return self.inspectblocktype(NifFormat.NiSequence)
        
    def branchinspect(self, branch):
        # inspect the NiAVObject and NiSequence branches
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiSequence))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiSequence):
            for controlled_block in branch.controlled_blocks:
                if controlled_block.get_node_name().lower() in self.toaster.change_blocks:
                    self.data.replace_global_node(controlled_block.interpolator.data, None)
                    self.toaster.msg("NiTransformData removed from interpolator for %s" % (controlled_block.get_node_name()))
                    self.changed = True
        return True

class SpellCollisionToMopp(NifSpell):
    """Transforms non-mopp triangle collisions to the more efficient mopps."""

    SPELLNAME = "modify_collisiontomopp"
    READONLY = False

    def datainspect(self):
        return self.inspectblocktype(NifFormat.bhkRigidBody)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRigidBody))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.bhkRigidBody):
            if isinstance(branch.shape, (NifFormat.bhkNiTriStripsShape,
                                         NifFormat.bhkPackedNiTriStripsShape)):
                colmopp = NifFormat.bhkMoppBvTreeShape()
                colmopp.material = branch.shape.material
                colmopp.unknown_8_bytes[0] = 160
                colmopp.unknown_8_bytes[1] = 13
                colmopp.unknown_8_bytes[2] = 75
                colmopp.unknown_8_bytes[3] = 1
                colmopp.unknown_8_bytes[4] = 192
                colmopp.unknown_8_bytes[5] = 207
                colmopp.unknown_8_bytes[6] = 144
                colmopp.unknown_8_bytes[7] = 11
                colmopp.unknown_float = 1.0
                if isinstance(branch.shape, NifFormat.bhkNiTriStripsShape):
                    branch.shape = branch.shape.get_interchangeable_packed_shape()
                colmopp.shape = branch.shape
                branch.shape = colmopp
                self.changed = True
                branch.shape.update_mopp()
                self.toaster.msg("collision set to MOPP")
            # Don't need to recurse further
            return False
        else:
            # recurse further
            return True

class SpellMirrorAnimation(NifSpell):
    """Mirrors the animation by switching bones and mirroring their x values. 
    Only useable on creature/character animations (well any animations
    as long as they have bones in the form of bip01/2 L ...).
    """

    SPELLNAME = "modify_mirroranimation"
    READONLY = False

    def datainspect(self):
        # returns more than needed but easiest way to ensure it catches all
        # types of animations
        return True
        
    def dataentry(self):
        # make list of used bones
        self.old_bone_data = {}
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiControllerSequence):
                for block in branch.controlled_blocks:
                    name = block.get_node_name().lower()
                    if ' r ' in name or ' l ' in name:
                        self.old_bone_data[name] = [block.interpolator, block.controller, block.priority, block.string_palette, block.node_name_offset, block.controller_type_offset]
        if self.old_bone_data:
            return True

    def branchinspect(self, branch):
        # inspect the NiAVObject branch, and NiControllerSequence
        # branch (for kf files)
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTimeController,
                                   NifFormat.NiInterpolator,
                                   NifFormat.NiControllerManager,
                                   NifFormat.NiControllerSequence))

    def branchentry(self, branch):
        old_bone_data = self.old_bone_data
                
        if isinstance(branch, NifFormat.NiControllerSequence):
            for block in branch.controlled_blocks:
                node_name = block.get_node_name().lower()
                if ' l ' in node_name: node_name = node_name.replace(' l ', ' r ')
                elif ' r ' in node_name: node_name = node_name.replace(' r ', ' l ')
                if node_name in old_bone_data:
                    self.changed = True
                    block.interpolator, block.controller, block.priority, block.string_palette, block.node_name_offset, block.controller_type_offset = old_bone_data[node_name]
                    # and then reverse x movements (since otherwise the movement of f.e. an arm towards the center of the body will be still in the same direction but away from the body
                    if not block.interpolator: continue
                    ip = block.interpolator
                    ip.translation.x = -ip.translation.x
                    ip.rotation.x = -ip.rotation.x
                    if ip.data:
                        data = ip.data
                        if data.translations.num_keys:
                            for key in data.translations.keys:
                                key.value.x = -key.value.x
                        if data.rotation_type == 4:
                            if data.xyz_rotations[1].num_keys != 0:
                                for key in data.xyz_rotations[1].keys:
                                    key.value = -key.value
                        elif data.num_rotation_keys != 0:
                            for key in data.quaternion_keys:
                                key.value.x = -key.value.x
        else:
            # recurse further
            return True
