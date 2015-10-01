"""Spells for optimizing nif files.

.. autoclass:: SpellCleanRefLists
   :show-inheritance:
   :members:

.. autoclass:: SpellMergeDuplicates
   :show-inheritance:
   :members:

.. autoclass:: SpellOptimizeGeometry
   :show-inheritance:
   :members:

.. autoclass:: SpellOptimize
   :show-inheritance:
   :members:

.. autoclass:: SpellDelUnusedBones
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

from itertools import izip
import os.path # exists

from pyffi.formats.nif import NifFormat
from pyffi.utils import unique_map
import pyffi.utils.tristrip
import pyffi.utils.vertex_cache
import pyffi.spells
import pyffi.spells.nif
import pyffi.spells.nif.fix
import pyffi.spells.nif.modify

# localization
#import gettext
#_ = gettext.translation('pyffi').ugettext
_ = lambda msg: msg # stub, for now

# set flag to overwrite files
__readonly__ = False

# example usage
__examples__ = """* Standard usage:

    python niftoaster.py optimize /path/to/copy/of/my/nifs

* Optimize, but do not merge NiMaterialProperty blocks:

    python niftoaster.py optimize --exclude=NiMaterialProperty /path/to/copy/of/my/nifs
"""

class SpellCleanRefLists(pyffi.spells.nif.NifSpell):
    """Remove empty and duplicate entries in reference lists."""

    SPELLNAME = "opt_cleanreflists"
    READONLY = False

    def datainspect(self):
        # see MadCat221's metstaff.nif:
        # merging data on PSysMeshEmitter affects particle system
        # so do not merge child links on this nif (probably we could still
        # merge other things: this is just a quick hack to make sure the
        # optimizer won't do anything wrong)
        try:
            if self.data.header.has_block_type(NifFormat.NiPSysMeshEmitter):
                return False
        except ValueError:
            # when in doubt, assume it does not have this block
            pass
        # so far, only reference lists in NiObjectNET blocks, NiAVObject
        # blocks, and NiNode blocks are checked
        return self.inspectblocktype(NifFormat.NiObjectNET)

    def dataentry(self):
        self.data.roots = self.cleanreflist(self.data.roots, "root")
        return True

    def branchinspect(self, branch):
        # only inspect the NiObjectNET branch
        return isinstance(branch, NifFormat.NiObjectNET)

    def cleanreflist(self, reflist, category):
        """Return a cleaned copy of the given list of references."""
        # delete empty and duplicate references
        cleanlist = []
        for ref in reflist:
            if ref is None:
                self.toaster.msg("removing empty %s reference" % category)
                self.changed = True
            elif ref in cleanlist:
                self.toaster.msg("removing duplicate %s reference" % category)
                self.changed = True
            else:
                cleanlist.append(ref)
        # done
        return cleanlist

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiObjectNET):
            # clean extra data
            branch.set_extra_datas(
                self.cleanreflist(branch.get_extra_datas(), "extra"))
        if isinstance(branch, NifFormat.NiAVObject):
            # clean properties
            branch.set_properties(
                self.cleanreflist(branch.get_properties(), "property"))
        if isinstance(branch, NifFormat.NiNode):
            # clean children
            branch.set_children(
                self.cleanreflist(branch.get_children(), "child"))
            # clean effects
            branch.set_effects(
                self.cleanreflist(branch.get_effects(), "effect"))
        # always recurse further
        return True

class SpellMergeDuplicates(pyffi.spells.nif.NifSpell):
    """Remove duplicate branches."""

    SPELLNAME = "opt_mergeduplicates"
    READONLY = False

    def __init__(self, *args, **kwargs):
        pyffi.spells.nif.NifSpell.__init__(self, *args, **kwargs)
        # list of all branches visited so far
        self.branches = []

    def datainspect(self):
        # see MadCat221's metstaff.nif:
        # merging data on PSysMeshEmitter affects particle system
        # so do not merge shapes on this nif (probably we could still
        # merge other things: this is just a quick hack to make sure the
        # optimizer won't do anything wrong)
        try:
            return not self.data.header.has_block_type(
                NifFormat.NiPSysMeshEmitter)
        except ValueError:
            # when in doubt, do the spell
            return True

    def branchinspect(self, branch):
        # only inspect the NiObjectNET branch (merging havok can mess up things)
        return isinstance(branch, (NifFormat.NiObjectNET,
                                   NifFormat.NiGeometryData))

    def branchentry(self, branch):
        for otherbranch in self.branches:
            if (branch is not otherbranch and
                branch.is_interchangeable(otherbranch)):
                # skip properties that have controllers (the
                # controller data cannot always be reliably checked,
                # see also issue #2106668)
                if (isinstance(branch, NifFormat.NiProperty)
                    and branch.controller):
                    continue
                # skip BSShaderProperty blocks (see niftools issue #3009832)
                if isinstance(branch, NifFormat.BSShaderProperty):
                    continue
                # interchangeable branch found!
                self.toaster.msg("removing duplicate branch")
                self.data.replace_global_node(branch, otherbranch)
                self.changed = True
                # branch has been replaced, so no need to recurse further
                return False
        else:
            # no duplicate found, add to list of visited branches
            self.branches.append(branch)
            # continue recursion
            return True

class SpellOptimizeGeometry(pyffi.spells.nif.NifSpell):
    """Optimize all geometries:
      - remove duplicate vertices
      - triangulate
      - recalculate skin partition
      - recalculate tangent space 
    """

    SPELLNAME = "opt_geometry"
    READONLY = False

    # spell parameters
    VERTEXPRECISION = 3
    NORMALPRECISION = 3
    UVPRECISION = 5
    VCOLPRECISION = 3

    def __init__(self, *args, **kwargs):
        pyffi.spells.nif.NifSpell.__init__(self, *args, **kwargs)
        # list of all optimized geometries so far
        # (to avoid optimizing the same geometry twice)
        self.optimized = []

    def datainspect(self):
        # do not optimize if an egm or tri file is detected
        filename = self.stream.name
        if (os.path.exists(filename[:-3] + "egm")
            or os.path.exists(filename[:-3] + "tri")):
            return False
        # so far, only reference lists in NiObjectNET blocks, NiAVObject
        # blocks, and NiNode blocks are checked
        return self.inspectblocktype(NifFormat.NiTriBasedGeom)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)

    def optimize_vertices(self, data):
        self.toaster.msg("removing duplicate vertices")
        # get map, deleting unused vertices
        return unique_map(
            vhash
            for i, vhash in enumerate(data.get_vertex_hash_generator(
                vertexprecision=self.VERTEXPRECISION,
                normalprecision=self.NORMALPRECISION,
                uvprecision=self.UVPRECISION,
                vcolprecision=self.VCOLPRECISION)))

    def branchentry(self, branch):
        """Optimize a NiTriStrips or NiTriShape block:
          - remove duplicate vertices
          - retriangulate for vertex cache
          - recalculate skin partition
          - recalculate tangent space 

        @todo: Limit the length of strips (see operation optimization mod for
            Oblivion!)
        """
        if not isinstance(branch, NifFormat.NiTriBasedGeom):
            # keep recursing
            return True

        if branch in self.optimized:
            # already optimized
            return False

        if branch.data.additional_data:
            # occurs in fallout nv
            # not sure how to deal with additional data
            # so skipping to be on the safe side
            self.toaster.msg(
                "mesh has additional geometry data"
                " which is not well understood: not optimizing")
            return False
    
        # we found a geometry to optimize

        # we're going to change the data
        self.changed = True

        # cover degenerate case
        if branch.data.num_vertices < 3 or branch.data.num_triangles == 0:
            self.toaster.msg(
                "less than 3 vertices or no triangles: removing branch")
            self.data.replace_global_node(branch, None)
            return False

        self.optimized.append(branch)

        # shortcut
        data = branch.data

        v_map, v_map_inverse = self.optimize_vertices(data)
        
        self.toaster.msg("(num vertices was %i and is now %i)"
                         % (len(v_map), len(v_map_inverse)))

        # optimizing triangle ordering
        # first, get new triangle indices, with duplicate vertices removed
        triangles = list(pyffi.utils.vertex_cache.get_unique_triangles(
            (v_map[v0], v_map[v1], v_map[v2])
            for v0, v1, v2 in data.get_triangles()))
        old_atvr = pyffi.utils.vertex_cache.average_transform_to_vertex_ratio(
            triangles)
        self.toaster.msg("optimizing triangle ordering")
        new_triangles = pyffi.utils.vertex_cache.get_cache_optimized_triangles(
            triangles)
        new_atvr = pyffi.utils.vertex_cache.average_transform_to_vertex_ratio(
            new_triangles)
        if new_atvr < old_atvr:
            triangles = new_triangles
            self.toaster.msg(
                "(ATVR reduced from %.3f to %.3f)" % (old_atvr, new_atvr))
        else:
            self.toaster.msg(
                "(ATVR stable at %.3f)" % old_atvr)            
        # optimize triangles to have sequentially ordered indices
        self.toaster.msg("optimizing vertex ordering")
        v_map_opt = pyffi.utils.vertex_cache.get_cache_optimized_vertex_map(
            triangles)
        triangles = [(v_map_opt[v0], v_map_opt[v1], v_map_opt[v2])
                      for v0, v1, v2 in triangles]
        # update vertex map and its inverse
        for i in xrange(data.num_vertices):
            try:
                v_map[i] = v_map_opt[v_map[i]]
            except IndexError:
                # found a trailing vertex which is not used
                v_map[i] = None
            if v_map[i] is not None:
                v_map_inverse[v_map[i]] = i
            else:
                self.toaster.logger.warn("unused vertex")
        try:
            new_numvertices = max(v for v in v_map if v is not None) + 1
        except ValueError:
            # max() arg is an empty sequence
            # this means that there are no vertices
            self.toaster.msg(
                "less than 3 vertices or no triangles: removing branch")
            self.data.replace_global_node(branch, None)
            return False
        del v_map_inverse[new_numvertices:]

        # use a triangle representation
        if not isinstance(branch, NifFormat.NiTriShape):
            self.toaster.msg("replacing branch by NiTriShape")
            newbranch = branch.get_interchangeable_tri_shape(
                triangles=triangles)
            self.data.replace_global_node(branch, newbranch)
            branch = newbranch
            data = newbranch.data
        else:
            data.set_triangles(triangles)

        # copy old data
        oldverts = [(v.x, v.y, v.z) for v in data.vertices]
        oldnorms = [(n.x, n.y, n.z) for n in data.normals]
        olduvs   = [[(uv.u, uv.v) for uv in uvset] for uvset in data.uv_sets]
        oldvcols = [(c.r, c.g, c.b, c.a) for c in data.vertex_colors]
        if branch.skin_instance: # for later
            oldweights = branch.get_vertex_weights()
        # set new data
        data.num_vertices = new_numvertices
        if data.has_vertices:
            data.vertices.update_size()
            for i, v in enumerate(data.vertices):
                old_i = v_map_inverse[i]
                v.x = oldverts[old_i][0]
                v.y = oldverts[old_i][1]
                v.z = oldverts[old_i][2]
        if data.has_normals:
            data.normals.update_size()
            for i, n in enumerate(data.normals):
                old_i = v_map_inverse[i]
                n.x = oldnorms[old_i][0]
                n.y = oldnorms[old_i][1]
                n.z = oldnorms[old_i][2]
        # XXX todo: if ...has_uv_sets...:
        data.uv_sets.update_size()
        for j, uvset in enumerate(data.uv_sets):
            for i, uv in enumerate(uvset):
                old_i = v_map_inverse[i]
                uv.u = olduvs[j][old_i][0]
                uv.v = olduvs[j][old_i][1]
        if data.has_vertex_colors:
            data.vertex_colors.update_size()
            for i, c in enumerate(data.vertex_colors):
                old_i = v_map_inverse[i]
                c.r = oldvcols[old_i][0]
                c.g = oldvcols[old_i][1]
                c.b = oldvcols[old_i][2]
                c.a = oldvcols[old_i][3]
        del oldverts
        del oldnorms
        del olduvs
        del oldvcols

        # update skin data
        if branch.skin_instance:
            self.toaster.msg("update skin data vertex mapping")
            skindata = branch.skin_instance.data
            newweights = []
            for i in xrange(new_numvertices):
                newweights.append(oldweights[v_map_inverse[i]])
            for bonenum, bonedata in enumerate(skindata.bone_list):
                w = []
                for i, weightlist in enumerate(newweights):
                    for bonenum_i, weight_i in weightlist:
                        if bonenum == bonenum_i:
                            w.append((i, weight_i))
                bonedata.num_vertices = len(w)
                bonedata.vertex_weights.update_size()
                for j, (i, weight_i) in enumerate(w):
                    bonedata.vertex_weights[j].index = i
                    bonedata.vertex_weights[j].weight = weight_i

            # update skin partition (only if branch already exists)
            if branch.get_skin_partition():
                self.toaster.msg("updating skin partition")
                if isinstance(branch.skin_instance,
                              NifFormat.BSDismemberSkinInstance):
                    # get body part indices (in the old system!)
                    triangles, trianglepartmap = (
                        branch.skin_instance.get_dismember_partitions())
                    maximize_bone_sharing = True
                    # update mapping
                    new_triangles = []
                    new_trianglepartmap = []
                    for triangle, trianglepart in izip(triangles, trianglepartmap):
                        new_triangle = tuple(v_map[i] for i in triangle)
                        # it could happen that v_map[i] is None
                        # these triangles are skipped
                        # see for instance
                        # falloutnv/meshes/armor/greatkhans/greatkhan_v3.nif
                        # falloutnv/meshes/armor/tunnelsnake01/m/outfitm.nif
                        if None not in new_triangle:
                            new_triangles.append(new_triangle)
                            new_trianglepartmap.append(trianglepart)
                    triangles = new_triangles
                    trianglepartmap = new_trianglepartmap
                else:
                    # no body parts
                    triangles = None
                    trianglepartmap = None
                    maximize_bone_sharing = False
                # use Oblivion settings
                branch.update_skin_partition(
                    maxbonesperpartition=18, maxbonespervertex=4,
                    stripify=False, verbose=0,
                    triangles=triangles, trianglepartmap=trianglepartmap,
                    maximize_bone_sharing=maximize_bone_sharing)

        # update morph data
        for morphctrl in branch.get_controllers():
            if isinstance(morphctrl, NifFormat.NiGeomMorpherController):
                morphdata = morphctrl.data
                # skip empty morph data
                if not morphdata:
                    continue
                # convert morphs
                self.toaster.msg("updating morphs")
                # check size and fix it if needed
                # (see issue #3395484 reported by rlibiez)
                # remap of morph vertices works only if
                # morph.num_vertices == len(v_map)
                if morphdata.num_vertices != len(v_map):
                    self.toaster.logger.warn(
                        "number of vertices in morph ({0}) does not match"
                        " number of vertices in shape ({1}):"
                        " resizing morph, graphical glitches might result"
                        .format(morphdata.num_vertices, len(v_map)))
                    morphdata.num_vertices = len(v_map)
                    for morph in morphdata.morphs:
                        morph.arg = morphdata.num_vertices # manual argument passing
                        morph.vectors.update_size()
                # now remap morph vertices
                for morph in morphdata.morphs:
                    # store a copy of the old vectors
                    oldmorphvectors = [(vec.x, vec.y, vec.z)
                                       for vec in morph.vectors]
                    for old_i, vec in izip(v_map_inverse, morph.vectors):
                        vec.x = oldmorphvectors[old_i][0]
                        vec.y = oldmorphvectors[old_i][1]
                        vec.z = oldmorphvectors[old_i][2]
                    del oldmorphvectors
                # resize matrices
                morphdata.num_vertices = new_numvertices
                for morph in morphdata.morphs:
                    morph.arg = morphdata.num_vertices # manual argument passing
                    morph.vectors.update_size()

        # recalculate tangent space (only if the branch already exists)
        if (branch.find(block_name='Tangent space (binormal & tangent vectors)',
                        block_type=NifFormat.NiBinaryExtraData)
            or (data.num_uv_sets & 61440)
            or (data.bs_num_uv_sets & 61440)):
            self.toaster.msg("recalculating tangent space")
            branch.update_tangent_space()

        # stop recursion
        return False

# XXX todo
class SpellSplitGeometry(pyffi.spells.nif.NifSpell):
    """Optimize geometry by splitting large models into pieces.
    (This spell is not yet fully implemented!)
    """
    SPELLNAME = "opt_split"
    READONLY = False
    THRESHOLD_RADIUS = 100 #: Threshold where to split geometry.

    # XXX todo
    @staticmethod
    def addVertex(sourceindex, v_map, sourcedata, destdata):
        """Add a vertex from source to destination. Returns index in
        destdata of the vertex."""
        # v_map maps source indices that have already been added to the
        # index they already have in the destdata

        # has_normals, num_uv_sets, etc. of destdata must already match
        # the sourcedata
        try:
            return v_map[sourceindex]
        except KeyError:
            v_map[sourceindex] = destdata.num_vertices
            destdata.num_vertices += 1
            destdata.vertices.update_size()
            destdata.vertices[-1].x = sourcedata.vertices[sourceindex].x
            destdata.vertices[-1].y = sourcedata.vertices[sourceindex].y
            destdata.vertices[-1].z = sourcedata.vertices[sourceindex].z
            if sourcedata.has_normals:
                destdata.normals.update_size()
                destdata.normals[-1].x = sourcedata.normals[sourceindex].x
                destdata.normals[-1].y = sourcedata.normals[sourceindex].y
                destdata.normals[-1].z = sourcedata.normals[sourceindex].z
            if sourcedata.has_vertex_colors:
                destdata.vertex_colors.update_size()
                destdata.vertex_colors[-1].r = sourcedata.vertex_colors[sourceindex].r
                destdata.vertex_colors[-1].g = sourcedata.vertex_colors[sourceindex].g
                destdata.vertex_colors[-1].b = sourcedata.vertex_colors[sourceindex].b
                destdata.vertex_colors[-1].a = sourcedata.vertex_colors[sourceindex].a
            if sourcedata.has_uv:
                for sourceuvset, destuvset in izip(sourcedata.uv_sets, destdata.uv_sets):
                    destuvset.update_size()
                    destuvset[-1].u = sourceuvset[sourceindex].u
                    destuvset[-1].v = sourceuvset[sourceindex].v
            return destdata.num_vertices

    # XXX todo
    @staticmethod
    def addTriangle(sourcetriangle, v_map, sourcedata, destdata):
        """Add a triangle from source to destination."""
        desttriangle = [
            destdata.addVertex(sourceindex)
            for sourceindex in sourcetriangle]
        destdata.num_triangles += 1
        destdata.triangles.update_size()
        destdata.triangles[-1].v_1 = desttriangle[0]
        destdata.triangles[-1].v_2 = desttriangle[0]
        destdata.triangles[-1].v_3 = desttriangle[0]

    # XXX todo
    @staticmethod
    def get_size(vertices, triangle):
        """Calculate size of geometry data + given triangle."""
        def helper(oper, coord):
            return oper((getattr(vert, coord) for vert in triangle),
                        oper(getattr(vert, coord) for vert in vertices))
        minx = helper(min, "x")
        miny = helper(min, "y")
        minz = helper(min, "z")
        maxx = helper(max, "x")
        maxy = helper(max, "y")
        maxz = helper(max, "z")
        return max((maxx - minx, maxy - miny, maxz - minz))

    # XXX todo: merge into branchentry spell
    @staticmethod
    def split(geom, threshold_radius = THRESHOLD_RADIUS):
        """Takes a NiGeometry block and splits the geometries. Returns a NiNode
        which contains the splitted geometry. Note that everything is triangulated
        in the process."""
        # make list of triangles
        # this will be used as the list of triangles still to add
        triangles = geom.data.get_triangles()
        node = NifFormat.NiNode().deepcopy(
            NifFormat.NiAVObject.deepcopy(geom))
        geomsplit = None
        # while there are still triangles to add...
        while triangles:
            if geomsplit is None:
                # split new geometry
                geomsplit = NifFormat.NiTriShape()
                node.add_child(geomsplit)
                geomsplit.data = NifFormat.NiTriShapeData()
                v_map = {}
                # copy relevant data
                geomsplit.name = "%s:%i" % (geom.name, node.num_children - 1)
                geomsplit.data.has_vertices = geom.data.has_vertices
                geomsplit.data.has_normals = geom.data.has_normals
                geomsplit.data.has_vertex_colors = geom.data.has_vertex_colors
                geomsplit.data.num_uv_sets = geom.data.num_uv_sets
                geomsplit.data.has_uv = geom.data.has_uv
                geomsplit.data.uv_sets.update_size()
                # assign it a random triangle
                triangle = triangles.pop(0)
                addTriangle(triangle, v_map, geom.data, geomsplit.data)
            # find face that is close to current geometry
            for triangle in triangles:
                 if get_size(geomsplit.data,
                            tuple(geom.data.vertices[index]
                                  for index in triangle)) < threshold_radius:
                     addTriangle(triangle, v_map, geom.data, geomsplit.data)
                     break
            else:
                # if exceeded, start new geometry
                # first finish some things in geomsplit data
                geomsplit.data.update_center_radius()
                # setting geomsplit to None flags this for
                # the next iteration
                geomsplit = None
        # return grouping node
        return node

    def __init__(self, *args, **kwargs):
        pyffi.spells.nif.NifSpell.__init__(self, *args, **kwargs)
        # list of all optimized geometries so far
        # (to avoid optimizing the same geometry twice)
        self.optimized = []

    def datainspect(self):
        return self.inspectblocktype(NifFormat.NiTriBasedGeom)

    def branchinspect(self, branch):
        return isinstance(branch, NifFormat.NiAVObject)

    def branchentry(self, branch):
        if not isinstance(branch, NifFormat.NiTriBasedGeom):
            # keep recursing
            return True

        if branch in self.optimized:
            # already optimized
            return False
    
        # we found a geometry to optimize
        # XXX todo
        # get geometry data
        geomdata = block.data
        if not geomdata:
            self.optimized.append(block)
            return False
        # check radius
        if geomdata.radius < self.THRESHOLD_RADIUS:
            optimized_geometries.append(block)
            return False
        # radius is over the threshold, so re-organize the geometry
        newblock = split(block, threshold_radius = THRESHOLD_RADIUS)
        # replace block with newblock everywhere
        data.replace_global_node(block, newblock)

        self.optimized.append(block)

        # stop recursing
        return False

class SpellDelUnusedBones(pyffi.spells.nif.NifSpell):
    """Remove nodes that are not used for anything."""

    SPELLNAME = "opt_delunusedbones"
    READONLY = False

    def datainspect(self):
        # only run the spell if there are skinned geometries
        return self.inspectblocktype(NifFormat.NiSkinInstance)

    def dataentry(self):
        # make list of used bones
        self._used_bones = set()
        for branch in self.data.get_global_iterator():
            if isinstance(branch, NifFormat.NiGeometry):
                if branch.skin_instance:
                    self._used_bones |= set(branch.skin_instance.bones)
        return True

    def branchinspect(self, branch):
        # only inspect the NiNode branch
        return isinstance(branch, NifFormat.NiNode)
    
    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiNode):
            if ((not branch.children)
                and (not branch.collision_object)
                and (branch not in self._used_bones)):
                self.toaster.msg("removing unreferenced bone")
                self.data.replace_global_node(branch, None)
                self.changed = True
                # no need to recurse further
                return False
        return True

class SpellDelZeroScale(pyffi.spells.nif.NifSpell):
    """Remove nodes with zero scale."""

    SPELLNAME = "opt_delzeroscale"
    READONLY = False

    def datainspect(self):
        # only run the spell if there are scaled objects
        return self.inspectblocktype(NifFormat.NiAVObject)

    def branchinspect(self, branch):
        # only inspect the NiAVObject branch
        return isinstance(branch, NifFormat.NiAVObject)
    
    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiAVObject):
            if branch.scale == 0:
                self.toaster.msg("removing zero scaled branch")
                self.data.replace_global_node(branch, None)
                self.changed = True
                # no need to recurse further
                return False
        return True

class SpellReduceGeometry(SpellOptimizeGeometry):
    """Reduce vertices of all geometries."""

    SPELLNAME = "opt_reducegeometry"
    READONLY = False
    
    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            toaster.logger.warn(
                "must specify degree of reduction as argument "
                "(e.g. 2 to reduce a little, 1 to reduce more, "
                "0 to reduce even more, -0.1 is usually the highest "
                "level of optimization possible before significant "
                " graphical oddities occur) to to apply spell")
            return False
        else:
            precision = float(toaster.options["arg"])
            cls.VERTEXPRECISION = precision
            cls.NORMALPRECISION = max(precision, 0)
            cls.UVPRECISION = max(precision, 0)
            cls.VCOLPRECISION = max(precision, 0)
            return True

class SpellOptimizeCollisionBox(pyffi.spells.nif.NifSpell):
    """Optimize collision geometries by converting shapes to primitive
    boxes where appropriate.
    """
    SPELLNAME = "opt_collisionbox"
    READONLY = False
    VERTEXPRECISION = 3

    def __init__(self, *args, **kwargs):
        pyffi.spells.nif.NifSpell.__init__(self, *args, **kwargs)
        # list of all optimized geometries so far
        # (to avoid optimizing the same geometry twice)
        self.optimized = []
        
    def datainspect(self):
        # only run the spell if there are collisions
        return (
            self.inspectblocktype(NifFormat.bhkPackedNiTriStripsShape)
            or self.inspectblocktype(NifFormat.bhkNiTriStripsShape))

    def branchinspect(self, branch):
        # only inspect the collision branches
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRigidBody,
                                   NifFormat.bhkMoppBvTreeShape))
        
    def get_box_shape(self, shape):
        """Check if the given shape is has a box shape. If so, return an
        equivalent (bhkConvexTransformShape +) bhkBoxShape.

        Shape should be a bhkPackedNiTriStripsShape or a bhkNiTriStripsShape.
        """
        PRECISION = 100

        # get vertices, triangles, and material
        if isinstance(shape, NifFormat.bhkPackedNiTriStripsShape):
            # multimaterial? cannot use a box
            if len(shape.get_sub_shapes()) != 1:
                return None
            vertices = shape.data.vertices
            triangles = [
                (hk_triangle.triangle.v_1,
                 hk_triangle.triangle.v_2,
                 hk_triangle.triangle.v_3)
                for hk_triangle in shape.data.triangles]
            material = shape.get_sub_shapes()[0].material
            factor = 1.0
        elif isinstance(shape, NifFormat.bhkNiTriStripsShape):
            if shape.num_strips_data != 1:
                return None
            vertices = shape.strips_data[0].vertices
            triangles = shape.strips_data[0].get_triangles()
            material = shape.material
            factor = 7.0
        # check triangles
        if len(triangles) != 12:
            return None
        # sorted vertices of a unit box
        unit_box = [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
                    (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]
        # sort vertices and rescale them to fit in the unit box
        verts = sorted(list(vert.as_tuple() for vert in vertices))
        min_ = [min(vert[i] for vert in verts) for i in range(3)]
        size = [max(vert[i] for vert in verts) - min_[i] for i in range(3)]
        if any((s < 1e-10) for s in size):
            # one of the dimensions is zero, so not a box
            return None
        scaled_verts = sorted(
            set(tuple(int(0.5 + PRECISION * ((vert[i] - min_[i]) / size[i]))
                      for i in range(3))
                for vert in verts))
        # if our vertices are a box, then the scaled_verts should coincide with
        # unit_box
        if len(scaled_verts) != 8:
            # cannot be a box
            return None
        non_boxiness = sum(sum(abs(PRECISION * vert[i] - othervert[i])
                               for i in range(3))
                           for vert, othervert in zip(unit_box, scaled_verts))
        if non_boxiness > 0:
            # not really a box, so return nothing
            return None
        # it is a box! replace by a bhkBoxShape
        boxshape = NifFormat.bhkBoxShape()
        boxshape.dimensions.x = size[0] / (2 * factor)
        boxshape.dimensions.y = size[1] / (2 * factor)
        boxshape.dimensions.z = size[2] / (2 * factor)
        boxshape.minimum_size = min(size) / factor
        try:
            boxshape.material = material
        except ValueError:
            # material has a bad value, this sometimes happens
            pass
        boxshape.radius = 0.1
        boxshape.unknown_8_bytes[0] = 0x6b
        boxshape.unknown_8_bytes[1] = 0xee
        boxshape.unknown_8_bytes[2] = 0x43
        boxshape.unknown_8_bytes[3] = 0x40
        boxshape.unknown_8_bytes[4] = 0x3a
        boxshape.unknown_8_bytes[5] = 0xef
        boxshape.unknown_8_bytes[6] = 0x8e
        boxshape.unknown_8_bytes[7] = 0x3e
        # check translation
        mid = [min_[i] + 0.5 * size[i] for i in range(3)]
        if sum(abs(mid[i]) for i in range(3)) < 1e-6:
            # no transform needed
            return boxshape
        else:
            # create transform block
            tfshape = NifFormat.bhkConvexTransformShape()
            tfshape.shape = boxshape
            tfshape.material = boxshape.material
            tfshape.transform.m_14 = mid[0] / factor
            tfshape.transform.m_24 = mid[1] / factor
            tfshape.transform.m_34 = mid[2] / factor
            return tfshape
        
    def branchentry(self, branch):
        """Optimize a vertex based collision block:
          - remove duplicate vertices
          - rebuild triangle indice and welding info
          - update MOPP data if applicable.
        """
        if branch in self.optimized:
            # already optimized
            return False
        
        if (isinstance(branch, NifFormat.bhkMoppBvTreeShape)
            and isinstance(branch.shape, NifFormat.bhkPackedNiTriStripsShape)
            and isinstance(branch.shape.data,
                           NifFormat.hkPackedNiTriStripsData)):
            # packed collision with mopp
            box_shape = self.get_box_shape(branch.shape)
            if box_shape:
                # it is a box, replace bhkMoppBvTreeShape
                self.data.replace_global_node(branch, box_shape)
                self.toaster.msg(_("optimized box collision"))
                self.changed = True
                self.optimized.append(branch)
            return False # don't recurse farther
        elif (isinstance(branch, NifFormat.bhkRigidBody)
              and isinstance(branch.shape, NifFormat.bhkNiTriStripsShape)):
            # unpacked collision
            box_shape = self.get_box_shape(branch.shape)
            if box_shape:
                # it is a box, replace bhkNiTriStripsShape
                self.data.replace_global_node(branch.shape, box_shape)
                self.toaster.msg(_("optimized box collision"))
                self.changed = True
                self.optimized.append(branch)
            # don't recurse further
            return False
        elif (isinstance(branch, NifFormat.bhkRigidBody)
              and isinstance(branch.shape,
                             NifFormat.bhkPackedNiTriStripsShape)):
            # packed collision without mopp
            box_shape = self.get_box_shape(branch.shape)
            if box_shape:
                # it's a box, replace bhkPackedNiTriStripsShape
                self.data.replace_global_node(branch.shape, box_shape)
                self.toaster.msg(_("optimized box collision"))
                self.changed = True
                self.optimized.append(branch)
            return False
        #keep recursing
        return True

class SpellOptimizeCollisionGeometry(pyffi.spells.nif.NifSpell):
    """Optimize collision geometries by removing duplicate vertices."""

    SPELLNAME = "opt_collisiongeometry"
    READONLY = False
    VERTEXPRECISION = 3

    def __init__(self, *args, **kwargs):
        pyffi.spells.nif.NifSpell.__init__(self, *args, **kwargs)
        # list of all optimized geometries so far
        # (to avoid optimizing the same geometry twice)
        self.optimized = []

    def datainspect(self):
        # only run the spell if there are collisions
        return (
            self.inspectblocktype(NifFormat.bhkPackedNiTriStripsShape)
            or self.inspectblocktype(NifFormat.bhkNiTriStripsShape))

    def branchinspect(self, branch):
        # only inspect the collision branches
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.bhkCollisionObject,
                                   NifFormat.bhkRigidBody,
                                   NifFormat.bhkMoppBvTreeShape))
        
    def optimize_mopp(self, mopp):
        """Optimize a bhkMoppBvTreeShape."""
        shape = mopp.shape
        data = shape.data

        # removing duplicate vertices
        self.toaster.msg(_("removing duplicate vertices"))
        # make a joint map for all subshapes
        # while doing this, also update subshape vertex count
        full_v_map = []
        full_v_map_inverse = []
        subshape_counts = []
        for subshape_index in range(len(shape.get_sub_shapes())):
            self.toaster.msg(_("(processing subshape %i)")
                             % subshape_index)
            v_map, v_map_inverse = unique_map(
                shape.get_vertex_hash_generator(
                    vertexprecision=self.VERTEXPRECISION,
                    subshape_index=subshape_index))
            self.toaster.msg(
                _("(num vertices in collision shape was %i and is now %i)")
                % (len(v_map), len(v_map_inverse)))
            # update subshape vertex count
            subshape_counts.append(len(v_map_inverse))
            # update full maps
            num_vertices = len(full_v_map_inverse)
            old_num_vertices = len(full_v_map)
            full_v_map += [num_vertices + i
                           for i in v_map]
            full_v_map_inverse += [old_num_vertices + old_i
                                   for old_i in v_map_inverse]
        # copy old data
        oldverts = [(v.x, v.y, v.z) for v in data.vertices]
        # set new subshape counts
        for subshape_index, subshape_count in enumerate(subshape_counts):
            if shape.sub_shapes:
                # oblivion subshapes
                shape.sub_shapes[subshape_index].num_vertices = subshape_count
            if shape.data.sub_shapes:
                # fallout 3 subshapes
                shape.data.sub_shapes[subshape_index].num_vertices = subshape_count            
        # set new data
        data.num_vertices = len(full_v_map_inverse)
        data.vertices.update_size()
        for old_i, v in izip(full_v_map_inverse, data.vertices):
            v.x = oldverts[old_i][0]
            v.y = oldverts[old_i][1]
            v.z = oldverts[old_i][2]
        del oldverts
        # update vertex indices in triangles
        for tri in data.triangles:
            tri.triangle.v_1 = full_v_map[tri.triangle.v_1]
            tri.triangle.v_2 = full_v_map[tri.triangle.v_2]
            tri.triangle.v_3 = full_v_map[tri.triangle.v_3]
        # at the moment recreating the mopp will destroy multi material mopps
        # (this is a bug in the mopper, not sure what it is)
        # so for now, we keep the mopp intact
        # and since the mopp code references the triangle indices
        # we must also keep the triangles intact
        if len(shape.get_sub_shapes()) != 1:
            return

        # remove duplicate triangles
        self.toaster.msg(_("removing duplicate triangles"))
        t_map, t_map_inverse = unique_map(shape.get_triangle_hash_generator())
        new_numtriangles = len(t_map_inverse)
        self.toaster.msg(_("(num triangles in collision shape was %i and is now %i)")
                         % (len(t_map), new_numtriangles))
        # copy old data
        oldtris = [(tri.triangle.v_1, tri.triangle.v_2, tri.triangle.v_3,
                    tri.normal.x, tri.normal.y, tri.normal.z)
                   for tri in data.triangles]
        # set new data
        data.num_triangles = new_numtriangles
        data.triangles.update_size()
        for old_i, tri in izip(t_map_inverse, data.triangles):
            if old_i is None:
                continue
            tri.triangle.v_1 = oldtris[old_i][0]
            tri.triangle.v_2 = oldtris[old_i][1]
            tri.triangle.v_3 = oldtris[old_i][2]
            tri.normal.x = oldtris[old_i][3]
            tri.normal.y = oldtris[old_i][4]
            tri.normal.z = oldtris[old_i][5]
            # note: welding updated later when calling the mopper
        del oldtris
        # update mopp data and welding info
        mopp.update_mopp_welding()
        
    def branchentry(self, branch):
        """Optimize a vertex based collision block:
          - remove duplicate vertices
          - rebuild triangle indices and welding info
          - update mopp data if applicable.

        (note: latter two are skipped at the moment due to
        multimaterial bug in mopper)
        """
        if branch in self.optimized:
            # already optimized
            return False

        if (isinstance(branch, NifFormat.bhkMoppBvTreeShape)
            and isinstance(branch.shape, NifFormat.bhkPackedNiTriStripsShape)
            and isinstance(branch.shape.data,
                           NifFormat.hkPackedNiTriStripsData)):
            # packed collision with mopp
            self.toaster.msg(_("optimizing mopp"))
            self.optimize_mopp(branch)
            if branch.shape.data.num_vertices < 3:
                self.toaster.msg(_("less than 3 vertices: removing branch"))
                self.data.replace_global_node(branch, None)
                self.changed = True
                return False
            self.optimized.append(branch)
            self.changed = True
            return False
        elif (isinstance(branch, NifFormat.bhkRigidBody)
              and isinstance(branch.shape, NifFormat.bhkNiTriStripsShape)):
            if branch.layer == NifFormat.OblivionLayer.OL_CLUTTER:
                # packed collisions do not work for clutter
                # so skip it
                # see issue #3194017 reported by Gratis_monsta
                return False
            # unpacked collision: convert to packed
            self.toaster.msg(_("packing collision"))
            new_shape = branch.shape.get_interchangeable_packed_shape()
            self.data.replace_global_node(branch.shape, new_shape)
            # call branchentry again in order to create a mopp for it
            # so we don't append it to self.optimized yet!!
            self.branchentry(branch)
            self.changed = True
            # don't recurse further
            return False
        elif (isinstance(branch, NifFormat.bhkRigidBody)
              and isinstance(branch.shape,
                             NifFormat.bhkPackedNiTriStripsShape)):
            # packed collision without mopp
            # add a mopp to it if it is static
            if any(sub_shape.layer != 1
                   for sub_shape in branch.shape.get_sub_shapes()):
                # no mopps for non-static objects
                return False
            self.toaster.msg(_("adding mopp"))
            mopp = NifFormat.bhkMoppBvTreeShape()
            shape = branch.shape # store reference before replacing
            self.data.replace_global_node(branch.shape, mopp)
            mopp.shape = shape
            mopp.material = shape.get_sub_shapes()[0].material
            mopp.unknown_8_bytes[0] = 160
            mopp.unknown_8_bytes[1] = 13
            mopp.unknown_8_bytes[2] = 75
            mopp.unknown_8_bytes[3] = 1
            mopp.unknown_8_bytes[4] = 192
            mopp.unknown_8_bytes[5] = 207
            mopp.unknown_8_bytes[6] = 144
            mopp.unknown_8_bytes[7] = 11
            mopp.unknown_float = 1.0
            mopp.update_mopp_welding()
            # call branchentry again in order to optimize the mopp
            # so we don't append it to self.optimized yet!!
            self.branchentry(mopp)
            self.changed = True
            return False
        # keep recursing
        return True
        
class SpellOptimizeAnimation(pyffi.spells.nif.NifSpell):
    """Optimizes animations by removing duplicate keys"""

    SPELLNAME = "opt_optimizeanimation"
    READONLY = False
    
    @classmethod
    def toastentry(cls, toaster):
        if not toaster.options["arg"]:
            cls.significance_check = 4
        else:
            cls.significance_check = float(toaster.options["arg"])
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

    def optimize_keys(self,keys):
        """Helper function to optimize the keys."""
        new_keys = []
        #compare keys
        ## types: 0 = float/int values
        ##        1 = Vector4, Quaternions, QuaternionsWXYZ
        ##        2 = word values (ie NiTextKeyExtraData)
        ##        3 = Vector3 values (ie translations)
        if len(keys) < 3: return keys # no optimization possible?
        precision = 10**self.significance_check
        if isinstance(keys[0].value,(float,int)):
            for i, key in enumerate(keys):
                if i == 0: # since we don't want to delete the first key even if it is  the same as the last key.
                    new_keys.append(key)
                    continue                
                try:
                    if int(precision*keys[i-1].value) != int(precision*key.value):
                        new_keys.append(key)
                        continue
                    if int(precision*keys[i+1].value) != int(precision*key.value):
                        new_keys.append(key)
                except IndexError:
                    new_keys.append(key)
            return new_keys
        elif isinstance(keys[0].value,(str)):
            for i, key in enumerate(keys):
                if i == 0: # since we don't want to delete the first key even if it is  the same as the last key.
                    new_keys.append(key)
                    continue 
                try:
                    if keys[i-1].value != key.value:
                        new_keys.append(key)
                        continue
                    if keys[i+1].value != key.value:
                        new_keys.append(key)
                except IndexError:
                    new_keys.append(key)
            return new_keys
        elif isinstance(keys[0].value,(NifFormat.Vector4,NifFormat.Quaternion,NifFormat.QuaternionXYZW)):
            tempkey = [[int(keys[0].value.w*precision),int(keys[0].value.x*precision),int(keys[0].value.y*precision),int(keys[0].value.z*precision)],[int(keys[1].value.w*precision),int(keys[1].value.x*precision),int(keys[1].value.y*precision),int(keys[1].value.z*precision)],[int(keys[2].value.w*precision),int(keys[2].value.x*precision),int(keys[2].value.y*precision),int(keys[2].value.z*precision)]]
            for i, key in enumerate(keys):
                if i == 0:
                    new_keys.append(key)
                    continue
                tempkey[0] = tempkey[1]
                tempkey[1] = tempkey[2]
                tempkey[2] = []
                try:
                    tempkey[2].append(int(keys[i+1].value.w*precision))
                    tempkey[2].append(int(keys[i+1].value.x*precision))
                    tempkey[2].append(int(keys[i+1].value.y*precision))
                    tempkey[2].append(int(keys[i+1].value.z*precision))
                except IndexError:
                    new_keys.append(key)
                    continue
                if tempkey[1] != tempkey[0]:
                    new_keys.append(key)
                    continue
                if tempkey[1] != tempkey[2]:
                    new_keys.append(key)
            return new_keys
        elif isinstance(keys[0].value,(NifFormat.Vector3)):
            tempkey = [[int(keys[0].value.x*precision),int(keys[0].value.y*precision),int(keys[0].value.z*precision)],[int(keys[1].value.x*precision),int(keys[1].value.y*precision),int(keys[1].value.z*precision)],[int(keys[2].value.x*precision),int(keys[2].value.y*precision),int(keys[2].value.z*precision)]]
            for i, key in enumerate(keys):
                if i == 0:
                    new_keys.append(key)
                    continue
                tempkey[0] = tempkey[1]
                tempkey[1] = tempkey[2]
                tempkey[2] = []
                try:
                    tempkey[2].append(int(keys[i+1].value.x*precision))
                    tempkey[2].append(int(keys[i+1].value.y*precision))
                    tempkey[2].append(int(keys[i+1].value.z*precision))
                except IndexError:
                    new_keys.append(key)
                    continue
                if tempkey[1] != tempkey[0]:
                    new_keys.append(key)
                    continue
                if tempkey[1] != tempkey[2]:
                    new_keys.append(key)
            return new_keys
        else: #something unhandled -- but what?
            
            return keys
            
    def update_animation(self,old_keygroup,new_keys):
        self.toaster.msg(_("Num keys was %i and is now %i") % (len(old_keygroup.keys),len(new_keys)))
        old_keygroup.num_keys = len(new_keys)
        old_keygroup.keys.update_size()
        for old_key, new_key in izip(old_keygroup.keys,new_keys):
            old_key.time = new_key.time
            old_key.value = new_key.value
        self.changed = True
        
    def update_animation_quaternion(self,old_keygroup,new_keys):
        self.toaster.msg(_("Num keys was %i and is now %i") % (len(old_keygroup),len(new_keys)))
        old_keygroup.update_size()
        for old_key, new_key in izip(old_keygroup,new_keys):
            old_key.time = new_key.time
            old_key.value = new_key.value
        self.changed = True

    def branchentry(self, branch):
            
        if isinstance(branch, NifFormat.NiKeyframeData):
            # (this also covers NiTransformData)
            if branch.num_rotation_keys != 0:
                if branch.rotation_type == 4:
                    for rotation in branch.xyz_rotations:
                        new_keys = self.optimize_keys(rotation.keys)
                        if len(new_keys) != rotation.num_keys:
                            self.update_animation(rotation,new_keys)
                else:
                    new_keys = self.optimize_keys(branch.quaternion_keys)
                    if len(new_keys) != branch.num_rotation_keys:
                        branch.num_rotation_keys = len(new_keys)
                        self.update_animation_quaternion(branch.quaternion_keys,new_keys)
            if branch.translations.num_keys != 0:
                new_keys = self.optimize_keys(branch.translations.keys)
                if len(new_keys) != branch.translations.num_keys:
                    self.update_animation(branch.translations,new_keys)
            if branch.scales.num_keys != 0:
                new_keys = self.optimize_keys(branch.scales.keys)
                if len(new_keys) != branch.scales.num_keys:
                    self.update_animation(branch.scales,new_keys)
            # no children of NiKeyframeData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiTextKeyExtraData):
            self.optimize_keys(branch.text_keys)
            # no children of NiTextKeyExtraData so no need to recurse further
            return False
        elif isinstance(branch, NifFormat.NiFloatData):
            #self.optimize_keys(branch.data.keys)
            # no children of NiFloatData so no need to recurse further
            return False
        else:
            # recurse further
            return True
        
class SpellOptimize(
    pyffi.spells.SpellGroupSeries(
        pyffi.spells.nif.modify.SpellCleanFarNif,
        pyffi.spells.SpellGroupParallel(
            pyffi.spells.nif.fix.SpellDelUnusedRoots,
            SpellCleanRefLists,
            pyffi.spells.nif.fix.SpellDetachHavokTriStripsData,
            pyffi.spells.nif.fix.SpellFixTexturePath,
            pyffi.spells.nif.fix.SpellClampMaterialAlpha,
            pyffi.spells.nif.fix.SpellFixBhkSubShapes,
            pyffi.spells.nif.fix.SpellFixEmptySkeletonRoots),
        SpellOptimizeGeometry,
        SpellOptimizeCollisionBox,
        SpellOptimizeCollisionGeometry,
        SpellMergeDuplicates,
        )):
    """Global fixer and optimizer spell."""
    SPELLNAME = "optimize"
