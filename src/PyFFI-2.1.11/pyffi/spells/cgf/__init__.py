"""
:mod:`pyffi.spells.cgf` ---  Crytek Geometry/Animation (.cgf/.cga) spells
=========================================================================

.. todo:: Write documentation.
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
from pyffi.formats.cgf import CgfFormat

class CgfSpell(pyffi.spells.Spell):
    """Base class for spells for cgf files."""

    def _datainspect(self):
        # call base method
        if not pyffi.spells.Spell._datainspect(self):
            return False

        # shortcut for common case (speeds up the check in most cases)
        if not self.toaster.include_types and not self.toaster.exclude_types:
            return True

        # check that at least one block type of the header is admissible
        return any(self.toaster.is_admissible_branch_class(header_type)
                   for header_type in self.data.chunk_table.get_chunk_types())

    def inspectblocktype(self, block_type):
        """This function heuristically checks whether the given block type
        is used in the cgf file, using header information only. When in doubt,
        it returns ``True``.

        :param block_type: The block type.
        :type block_type: L{CgfFormat.Chunk}
        :return: ``False`` if the cgf has no block of the given type,
            with certainty. ``True`` if the cgf has the block, or if it
            cannot be determined.
        :rtype: ``bool``
        """
        return (block_type in self.data.chunk_table.get_chunk_types())

class CgfToaster(pyffi.spells.Toaster):
    FILEFORMAT = CgfFormat

