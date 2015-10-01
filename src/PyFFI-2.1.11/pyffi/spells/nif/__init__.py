"""
:mod:`pyffi.spells.nif` ---  NetImmerse/Gamebryo File/Keyframe (.nif/.kf/.kfa) spells
=====================================================================================

.. automodule:: pyffi.spells.nif.check
.. automodule:: pyffi.spells.nif.dump
.. automodule:: pyffi.spells.nif.fix
.. automodule:: pyffi.spells.nif.optimize
.. automodule:: pyffi.spells.nif.modify
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

import pyffi.spells
from pyffi.formats.nif import NifFormat

class NifSpell(pyffi.spells.Spell):
    """Base class for spells for nif files."""

    def _datainspect(self):
        # list of all block types used in the header
        # (do this first, spells may depend on this being present)
        self.header_types = []
        for block_type in self.data.header.block_types:
            block_type = block_type.decode("ascii")
            # handle NiDataStream
            if block_type.startswith("NiDataStream\x01"):
                block_type = "NiDataStream"
            self.header_types.append(getattr(NifFormat, block_type))

        # call base method
        if not pyffi.spells.Spell._datainspect(self):
            return False

        # shortcut for common case (speeds up the check in most cases)
        if not self.toaster.include_types and not self.toaster.exclude_types:
            return True

        # old file formats have no list of block types
        # we cover that here
        if not self.header_types:
            return True

        # check that at least one block type of the header is admissible
        return any(self.toaster.is_admissible_branch_class(header_type)
                   for header_type in self.header_types)

    def inspectblocktype(self, block_type):
        """This function heuristically checks whether the given block type
        is used in the nif file, using header information only. When in doubt,
        it returns ``True``.

        :param block_type: The block type.
        :type block_type: :class:`NifFormat.NiObject`
        :return: ``False`` if the nif has no block of the given type,
            with certainty. ``True`` if the nif has the block, or if it
            cannot be determined.
        :rtype: ``bool``
        """
        try:
            # try via header
            return self.data.header.has_block_type(block_type)
        except ValueError:
            # header does not have the information because nif version is
            # too old
            return True

class SpellVisitSkeletonRoots(NifSpell):
    """Abstract base class for spells that visit all skeleton roots.
    Override the skelrootentry method with your implementation.
    """

    def datainspect(self):
        # only run the spell if there are skinned geometries
        return self.inspectblocktype(NifFormat.NiSkinInstance)

    def dataentry(self):
        # make list of skeleton roots
        self._skelroots = set()
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiGeometry):
                if branch.skin_instance:
                    skelroot = branch.skin_instance.skeleton_root
                    if skelroot and not(id(skelroot) in self._skelroots):
                        self._skelroots.add(id(skelroot))
        # only apply spell if there are skeleton roots
        if self._skelroots:
            return True
        else:
            return False

    def branchinspect(self, branch):
        # only inspect the NiNode branch
        return isinstance(branch, NifFormat.NiNode)
    
    def branchentry(self, branch):
        if id(branch) in self._skelroots:
            self.skelrootentry(branch)
            self._skelroots.remove(id(branch))
        # keep recursing into children if there are skeleton roots left
        return bool(self._skelroots)

    def skelrootentry(self, branch):
        """Do something with a skeleton root. Return value is ignored."""
        raise NotImplementedError

class NifToaster(pyffi.spells.Toaster):
    FILEFORMAT = NifFormat
