"""Algorithms to reorder triangle list order and vertex order aiming to
minimize vertex cache misses.

This is effectively an implementation of
'Linear-Speed Vertex Cache Optimisation' by Tom Forsyth, 28th September 2006
http://home.comcast.net/~tom_forsyth/papers/fast_vert_cache_opt.html
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

from __future__ import division

import collections

from pyffi.utils.tristrip import OrientedStrip

class VertexScore:
    """Vertex score calculation."""
    # constants used for scoring algorithm
    CACHE_SIZE = 32 # higher values yield virtually no improvement
    """The size of the modeled cache."""

    CACHE_DECAY_POWER = 1.5
    LAST_TRI_SCORE = 0.75
    VALENCE_BOOST_SCALE = 2.0
    VALENCE_BOOST_POWER = 0.5

    # implementation note: limitation of 255 triangles per vertex
    # this is unlikely to be exceeded...
    MAX_TRIANGLES_PER_VERTEX = 255

    def __init__(self):
        # calculation of score is precalculated for speed
        self.precalculate()

    def precalculate(self):
        self.CACHE_SCORE = [
            self.LAST_TRI_SCORE
            if cache_position < 3 else
            ((self.CACHE_SIZE - cache_position)
             / (self.CACHE_SIZE - 3)) ** self.CACHE_DECAY_POWER
            for cache_position in range(self.CACHE_SIZE)]

        self.VALENCE_SCORE = [
            self.VALENCE_BOOST_SCALE * (valence ** (-self.VALENCE_BOOST_POWER))
            if valence > 0 else None
            for valence in range(self.MAX_TRIANGLES_PER_VERTEX + 1)]

    def update_score(self, vertex_info):
        """Update score:

        * -1 if vertex has no triangles
        * cache score + valence score otherwise

        where cache score is

        * 0 if vertex is not in cache
        * 0.75 if vertex has been used very recently
          (position 0, 1, or 2)
        * (1 - (cache position - 3) / (32 - 3)) ** 1.5
          otherwise

        and valence score is 2 * (num triangles ** (-0.5))

        >>> vertex_score = VertexScore()
        >>> def get_score(cache_position, triangle_indices):
        ...     vert = VertexInfo(cache_position=cache_position,
        ...                       triangle_indices=triangle_indices)
        ...     vertex_score.update_score(vert)
        ...     return vert.score
        >>> for cache_position in [-1, 0, 1, 2, 3, 4, 5]:
        ...     print("cache position = {0}".format(cache_position))
        ...     for num_triangles in range(4):
        ...         print("  num triangles = {0} : {1:.3f}"
        ...               .format(num_triangles,
        ...                       get_score(cache_position,
        ...                                 list(range(num_triangles)))))
        cache position = -1
          num triangles = 0 : -1.000
          num triangles = 1 : 2.000
          num triangles = 2 : 1.414
          num triangles = 3 : 1.155
        cache position = 0
          num triangles = 0 : -1.000
          num triangles = 1 : 2.750
          num triangles = 2 : 2.164
          num triangles = 3 : 1.905
        cache position = 1
          num triangles = 0 : -1.000
          num triangles = 1 : 2.750
          num triangles = 2 : 2.164
          num triangles = 3 : 1.905
        cache position = 2
          num triangles = 0 : -1.000
          num triangles = 1 : 2.750
          num triangles = 2 : 2.164
          num triangles = 3 : 1.905
        cache position = 3
          num triangles = 0 : -1.000
          num triangles = 1 : 3.000
          num triangles = 2 : 2.414
          num triangles = 3 : 2.155
        cache position = 4
          num triangles = 0 : -1.000
          num triangles = 1 : 2.949
          num triangles = 2 : 2.363
          num triangles = 3 : 2.103
        cache position = 5
          num triangles = 0 : -1.000
          num triangles = 1 : 2.898
          num triangles = 2 : 2.313
          num triangles = 3 : 2.053
        """
        if not vertex_info.triangle_indices:
            # no triangle needs this vertex
            vertex_info.score = -1
            return

        if vertex_info.cache_position < 0:
            # not in cache
            vertex_info.score = 0
        else:
            # use cache score lookup table
            vertex_info.score = self.CACHE_SCORE[vertex_info.cache_position]

        # bonus points for having low number of triangles still in use
        # note: example mesh with more than 255 triangles per vertex is
        # falloutnv/meshes/landscape/lod/freesidefortworld/freesidefortworld.level8.x-9.y1.nif
        vertex_info.score += self.VALENCE_SCORE[
            min(len(vertex_info.triangle_indices),
                self.MAX_TRIANGLES_PER_VERTEX)]

class VertexInfo:
    """Stores information about a vertex."""

    def __init__(self, cache_position=-1, score=-1,
                 triangle_indices=None):
        self.cache_position = cache_position
        self.score = score
        # only triangles that have *not* yet been drawn are in this list
        self.triangle_indices = ([] if triangle_indices is None
                                 else triangle_indices)

class TriangleInfo:
    def __init__(self, score=0, vertex_indices=None):
        self.score = score
        self.vertex_indices = ([] if vertex_indices is None
                               else vertex_indices)

class Mesh:
    """Simple mesh implementation which keeps track of which triangles
    are used by which vertex, and vertex cache positions.
    """

    _DEBUG = False # to enable debugging of the algorithm

    def __init__(self, triangles, vertex_score=None):
        """Initialize mesh from given set of triangles.

        Empty mesh
        ----------

        >>> Mesh([]).triangle_infos
        []

        Single triangle mesh (with degenerate)
        --------------------------------------

        >>> m = Mesh([(0,1,2), (1,2,0)])
        >>> [vertex_info.triangle_indices for vertex_info in m.vertex_infos]
        [[0], [0], [0]]
        >>> [triangle_info.vertex_indices for triangle_info in m.triangle_infos]
        [(0, 1, 2)]

        Double triangle mesh
        --------------------

        >>> m = Mesh([(0,1,2), (2,1,3)])
        >>> [vertex_info.triangle_indices for vertex_info in m.vertex_infos]
        [[0], [0, 1], [0, 1], [1]]
        >>> [triangle_info.vertex_indices for triangle_info in m.triangle_infos]
        [(0, 1, 2), (1, 3, 2)]
        """
        # initialize vertex and triangle information, and vertex cache
        self.vertex_infos = []
        self.triangle_infos = []
        # add all vertices
        if triangles:
            num_vertices = max(max(verts) for verts in triangles) + 1
        else:
            num_vertices = 0
        # scoring algorithm
        if vertex_score is None:
            self.vertex_score = VertexScore()
        else:
            self.vertex_score = vertex_score
        self.vertex_infos = [VertexInfo() for i in xrange(num_vertices)]
        # add all triangles
        for triangle_index, verts in enumerate(get_unique_triangles(triangles)):
            self.triangle_infos.append(TriangleInfo(vertex_indices=verts))
            for vertex in verts:
                self.vertex_infos[vertex].triangle_indices.append(
                    triangle_index)
        # calculate score of all vertices
        for vertex_info in self.vertex_infos:
            self.vertex_score.update_score(vertex_info)
        # calculate score of all triangles
        for triangle_info in self.triangle_infos:
            triangle_info.score = sum(
                self.vertex_infos[vertex].score
                for vertex in triangle_info.vertex_indices)

    def get_cache_optimized_triangles(self):
        """Reorder triangles in a cache efficient way.

        >>> m = Mesh([(0,1,2), (7,8,9),(2,3,4)])
        >>> m.get_cache_optimized_triangles()
        [(7, 8, 9), (0, 1, 2), (2, 3, 4)]
        """
        triangles = []
        cache = collections.deque()
        # set of vertex indices whose scores were updated in the previous run
        updated_vertices = set()
        # set of triangle indices whose scores were updated in the previous run
        updated_triangles = set()
        while (updated_triangles
               or any(triangle_info for triangle_info in self.triangle_infos)):
            # pick triangle with highest score
            if self._DEBUG or not updated_triangles:
                # very slow but correct global maximum
                best_triangle_index, best_triangle_info = max(
                    (triangle
                     for triangle in enumerate(self.triangle_infos)
                     if triangle[1]),
                    key=lambda triangle: triangle[1].score)
            if updated_triangles:
                if self._DEBUG:
                    globally_optimal_score = best_triangle_info.score
                # if scores of triangles were updated in the previous run
                # then restrict the search to those
                # this is suboptimal, but the difference is usually very small
                # and it is *much* faster (as noted by Forsyth)
                best_triangle_index = max(
                    updated_triangles,
                    key=lambda triangle_index:
                    self.triangle_infos[triangle_index].score)
                best_triangle_info = self.triangle_infos[best_triangle_index]
                if (self._DEBUG and
                    globally_optimal_score - best_triangle_info.score > 0.01):
                        print(globally_optimal_score,
                              globally_optimal_score - best_triangle_info.score,
                              len(updated_triangles))
            # mark as added
            self.triangle_infos[best_triangle_index] = None
            # append to ordered list of triangles
            triangles.append(best_triangle_info.vertex_indices)
            # clean lists of vertices and triangles whose score we will update
            updated_vertices = set()
            updated_triangles = set()
            # for each vertex in the just added triangle
            for vertex in best_triangle_info.vertex_indices:
                vertex_info = self.vertex_infos[vertex]
                # remove triangle from the triangle list of the vertex
                vertex_info.triangle_indices.remove(best_triangle_index)
                # must update its score
                updated_vertices.add(vertex)
                updated_triangles.update(vertex_info.triangle_indices)
            # add each vertex to cache (score is updated later)
            for vertex in best_triangle_info.vertex_indices:
                if vertex not in cache:
                    cache.appendleft(vertex)
                    if len(cache) > self.vertex_score.CACHE_SIZE:
                        # cache overflow!
                        # remove vertex from cache
                        removed_vertex = cache.pop()
                        removed_vertex_info = self.vertex_infos[removed_vertex]
                        # update its cache position
                        removed_vertex_info.cache_position = -1
                        # must update its score
                        updated_vertices.add(removed_vertex)
                        updated_triangles.update(removed_vertex_info.triangle_indices)
            # for each vertex in the cache (this includes those from the
            # just added triangle)
            for i, vertex in enumerate(cache):
                vertex_info = self.vertex_infos[vertex]
                # update cache positions
                vertex_info.cache_position = i
                # must update its score
                updated_vertices.add(vertex)
                updated_triangles.update(vertex_info.triangle_indices)
            # update scores
            for vertex in updated_vertices:
                self.vertex_score.update_score(self.vertex_infos[vertex])
            for triangle in updated_triangles:
                triangle_info = self.triangle_infos[triangle]
                triangle_info.score = sum(
                    self.vertex_infos[vertex].score
                    for vertex in triangle_info.vertex_indices)
        # return result
        return triangles

def get_cache_optimized_triangles(triangles):
    """Calculate cache optimized triangles, and return the result as
    a reordered set of triangles or strip of stitched triangles.

    :param triangles: The triangles (triples of vertex indices).
    :return: A list of reordered triangles.
    """
    mesh = Mesh(triangles)
    return mesh.get_cache_optimized_triangles()

def get_unique_triangles(triangles):
    """Yield unique triangles.

    >>> list(get_unique_triangles([(0, 1, 2), (1, 1, 0), (2, 1, 0), (1, 0, 0)]))
    [(0, 1, 2), (0, 2, 1)]
    >>> list(get_unique_triangles([(0, 1, 2), (1, 1, 0), (2, 0, 1)]))
    [(0, 1, 2)]
    """
    _added_triangles = set()
    for v0, v1, v2 in triangles:
        if v0 == v1 or v1 == v2 or v2 == v0:
            # skip degenerate triangles
            continue
        if v0 < v1 and v0 < v2:
            verts = (v0, v1, v2)
        elif v1 < v0 and v1 < v2:
            verts = (v1, v2, v0)
        elif v2 < v0 and v2 < v1:
            verts = (v2, v0, v1)
        if verts not in _added_triangles:
            yield verts
            _added_triangles.add(verts)

def stable_stripify(triangles, stitchstrips=False):
    """Stitch all triangles together into a strip without changing the
    triangle ordering (for example because their ordering is already
    optimized).

    :param triangles: The triangles (triples of vertex indices).
    :return: A list of strips (list of vertex indices).

    >>> stable_stripify([(0, 1, 2), (2, 1, 4)])
    [[0, 1, 2, 4]]
    >>> stable_stripify([(0, 1, 2), (2, 3, 4)])
    [[0, 1, 2], [2, 3, 4]]
    >>> stable_stripify([(0, 1, 2), (2, 1, 3), (2, 3, 4), (1, 4, 5), (5, 4, 6)])
    [[0, 1, 2, 3, 4], [1, 4, 5, 6]]
    >>> stable_stripify([(0, 1, 2), (0, 3, 1), (0, 4, 3), (3, 5, 1), (6, 3, 4)])
    [[2, 0, 1, 3], [0, 4, 3], [3, 5, 1], [6, 3, 4]]
    """
    # all orientation preserving triangle permutations
    indices = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
    # list of all strips so far
    strips = []
    # current strip that is being built
    strip = []
    # add a triangle at a time
    for tri in triangles:
        if not strip:
            # empty strip
            strip.extend(tri)
        elif len(strip) == 3:
            # strip with single triangle
            # see if we can append a vertex
            # we can rearrange the original strip as well
            added = False
            for v0, v1, v2 in indices:
                for ov0, ov1, ov2 in indices:
                    if strip[v1] == tri[ov1] and  strip[v2] == tri[ov0]:
                        strip = [strip[v0], strip[v1], strip[v2], tri[ov2]]
                        added = True
                        break
                if added:
                    # triangle added: break loop
                    break
            if added:
                # triangle added: process next triangle
                continue
            # start new strip
            strips.append(strip)
            strip = list(tri)
        else:
            # strip with multiple triangles
            added = False
            for ov0, ov1, ov2 in indices:
                if len(strip) & 1:
                    if strip[-2] == tri[ov1] and  strip[-1] == tri[ov0]:
                        strip.append(tri[ov2])
                        added = True
                        break
                else:
                    if strip[-2] == tri[ov0] and  strip[-1] == tri[ov1]:
                        strip.append(tri[ov2])
                        added = True
                        break
            if added:
                # triangle added: process next triangle
                continue
            # start new strip
            strips.append(strip)
            strip = list(tri)
    # append last strip
    strips.append(strip)
    if not stitchstrips or not strips:
        return strips
    else:
        result = reduce(lambda x, y: x + y,
                        (OrientedStrip(strip) for strip in strips))
        return [list(result)]

def stripify(triangles, stitchstrips=False):
    """Stripify triangles, optimizing for the vertex cache."""
    return stable_stripify(
        get_cache_optimized_triangles(triangles),
        stitchstrips=stitchstrips)

def get_cache_optimized_vertex_map(strips):
    """Map vertices so triangles/strips have consequetive indices.

    >>> get_cache_optimized_vertex_map([])
    []
    >>> get_cache_optimized_vertex_map([[]])
    []
    >>> get_cache_optimized_vertex_map([[0, 1, 3], []])
    [0, 1, None, 2]
    >>> get_cache_optimized_vertex_map([(5,2,1),(0,2,3)])
    [3, 2, 1, 4, None, 0]
    """
    if strips:
        num_vertices = max(max(strip) if strip else -1
                           for strip in strips) + 1
    else:
        num_vertices = 0
    vertex_map = [None for i in xrange(num_vertices)]
    new_vertex = 0
    for strip in strips:
        for old_vertex in strip:
            if vertex_map[old_vertex] is None:
                vertex_map[old_vertex] = new_vertex
                new_vertex += 1
    return vertex_map

def average_transform_to_vertex_ratio(strips, cache_size=16):
    """Calculate number of transforms per vertex for a given cache size
    and triangles/strips. See
    http://castano.ludicon.com/blog/2009/01/29/acmr/
    """
    cache = collections.deque(maxlen=cache_size)
    # get number of vertices
    vertices = set([])
    for strip in strips:
        vertices.update(strip)
    # get number of cache misses (each miss needs a transform)
    num_misses = 0
    for strip in strips:
        for vertex in strip:
            if vertex in cache:
                pass
            else:
                cache.appendleft(vertex)
                num_misses += 1
    # return result
    if vertices:
        return num_misses / float(len(vertices))
    else:
        # no vertices...
        return 1

if __name__=='__main__':
    import doctest
    doctest.testmod()
