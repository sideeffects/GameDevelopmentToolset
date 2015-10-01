"""Module which contains all spells that check something in a cgf file."""

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

from itertools import izip
from tempfile import TemporaryFile

from pyffi.formats.cgf import CgfFormat
from pyffi.spells.cgf import CgfSpell
# XXX do something about this...
from pyffi.utils.mathutils import *

class SpellReadWrite(CgfSpell):
    """Like the original read-write spell, but with additional file size
    check."""

    SPELLNAME = "check_readwrite"

    def dataentry(self):
        self.toaster.msgblockbegin("writing to temporary file")
        f_tmp = TemporaryFile()
        try:
            total_padding = self.data.write(f_tmp)
            # comparing the files will usually be different because blocks may
            # have been written back in a different order, so cheaply just compare
            # file sizes
            self.toaster.msg("comparing file sizes")
            self.stream.seek(0, 2)
            f_tmp.seek(0, 2)
            if self.stream.tell() != f_tmp.tell():
                self.toaster.msg("original size: %i" % self.stream.tell())
                self.toaster.msg("written size:  %i" % f_tmp.tell())
                self.toaster.msg("padding:       %i" % total_padding)
                if self.stream.tell() > f_tmp.tell() or self.stream.tell() + total_padding < f_tmp.tell():
                    f_tmp.seek(0)
                    f_debug = open("debug.cgf", "wb")
                    f_debug.write(f_tmp.read(-1))
                    f_debug.close()
                    raise Exception('write check failed: file sizes differ by more than padding')
        finally:
            f_tmp.close()
        self.toaster.msgblockend()

        # spell is finished: prevent recursing into the tree
        return False

class SpellCheckTangentSpace(CgfSpell):
    """This spell checks the tangent space calculation.
    Only useful for debugging.
    """

    SPELLNAME = "check_tangentspace"
    SENSITIVITY = 0.1 # admissible float error (relative to one)

    def datainspect(self):
        return self.inspectblocktype(CgfFormat.MeshChunk)

    def branchinspect(self, branch):
        return isinstance(branch, (CgfFormat.MeshChunk, CgfFormat.NodeChunk))

    def branchentry(self, branch):
        if not isinstance(branch, CgfFormat.MeshChunk):            
            # keep recursing
            return True

        # get tangents and normals
        if not (branch.normals_data and branch.tangents_data):
            return True

        oldtangents = [tangent for tangent in branch.tangents_data.tangents]

        self.toaster.msg("recalculating new tangent space")
        branch.update_tangent_space()
        newtangents = [tangent for tangent in branch.tangents_data.tangents]

        self.toaster.msgblockbegin("validating and checking old with new")

        for norm, oldtangent, newtangent in izip(branch.normals_data.normals,
                                                 oldtangents, newtangents):
            #self.toaster.msg("*** %s ***" % (norm,))
            # check old
            norm = (norm.x, norm.y, norm.z)
            tan = tuple(x / 32767.0
                        for x in (oldtangent[0].x,
                                  oldtangent[0].y,
                                  oldtangent[0].z))
            bin = tuple(x / 32767.0
                        for x in (oldtangent[1].x,
                                  oldtangent[1].y,
                                  oldtangent[1].z))
            if abs(vecNorm(norm) - 1) > self.SENSITIVITY:
                self.toaster.logger.warn("normal has non-unit norm")
            if abs(vecNorm(tan) - 1) > self.SENSITIVITY:
                self.toaster.logger.warn("oldtangent has non-unit norm")
            if abs(vecNorm(bin) - 1) > self.SENSITIVITY:
                self.toaster.logger.warn("oldbinormal has non-unit norm")
            if (oldtangent[0].w != oldtangent[1].w):
                raise ValueError(
                    "inconsistent oldtangent w coordinate (%i != %i)"
                    % (oldtangent[0].w, oldtangent[1].w))
            if not (oldtangent[0].w in (-32767, 32767)):
                raise ValueError(
                    "invalid oldtangent w coordinate (%i)" % oldtangent[0].w)
            if oldtangent[0].w > 0:
                cross = vecCrossProduct(tan, bin)
            else:
                cross = vecCrossProduct(bin, tan)
            crossnorm = vecNorm(cross)
            if abs(crossnorm - 1) > self.SENSITIVITY:
                # a lot of these...
                self.toaster.logger.warn("tan and bin not orthogonal")
                self.toaster.logger.warn("%s %s" % (tan, bin))
                self.toaster.logger.warn("(error is %f)"
                                         % abs(crossnorm - 1))
                cross = vecscalarMul(cross, 1.0/crossnorm)
            if vecDistance(norm, cross) > self.SENSITIVITY:
                self.toaster.logger.warn(
                    "norm not cross product of tangent and binormal")
                #self.toaster.logger.warn("norm                 = %s" % (norm,))
                #self.toaster.logger.warn("tan                  = %s" % (tan,))
                #self.toaster.logger.warn("bin                  = %s" % (bin,))
                #self.toaster.logger.warn("tan bin cross prod   = %s" % (cross,))
                self.toaster.logger.warn(
                    "(error is %f)" % vecDistance(norm, cross))

            # compare old with new
            if sum((abs(oldtangent[0].x - newtangent[0].x),
                    abs(oldtangent[0].y - newtangent[0].y),
                    abs(oldtangent[0].z - newtangent[0].z),
                    abs(oldtangent[0].w - newtangent[0].w),
                    abs(oldtangent[1].x - newtangent[1].x),
                    abs(oldtangent[1].y - newtangent[1].y),
                    abs(oldtangent[1].z - newtangent[1].z),
                    abs(oldtangent[1].w - newtangent[1].w))) > self.SENSITIVITY * 32767.0:
                ntan = tuple(x / 32767.0 for x in (newtangent[0].x, newtangent[0].y, newtangent[0].z))
                nbin = tuple(x / 32767.0 for x in (newtangent[1].x, newtangent[1].y, newtangent[1].z))
                self.toaster.logger.warn("old and new tangents differ substantially")
                self.toaster.logger.warn("old tangent")
                self.toaster.logger.warn("%s %s" % (tan, bin))
                self.toaster.logger.warn("new tangent")
                self.toaster.logger.warn("%s %s" % (ntan, nbin))

        self.toaster.msgblockend()

class SpellCheckHasVertexColors(CgfSpell):
    """This spell checks if a model has vertex colors.
    Only useful for debugging.
    """
    # example: farcry/FCData/Objects/Buildings/M03/compound_area/coa_instantshelter_door_cloth.cgf

    SPELLNAME = "check_vcols"

    def datainspect(self):
        return self.inspectblocktype(CgfFormat.MeshChunk)

    def branchinspect(self, branch):
        return isinstance(branch, (CgfFormat.MeshChunk, CgfFormat.NodeChunk))

    def branchentry(self, branch):
        if isinstance(branch, CgfFormat.MeshChunk):
            if branch.has_vertex_colors:
                self.toaster.msg("has vertex colors!")
        else:
            # keep recursing
            return True
