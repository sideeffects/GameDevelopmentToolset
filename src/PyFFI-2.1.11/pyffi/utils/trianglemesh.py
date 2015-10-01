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

# modified from:

# http://techgame.net/projects/Runeblade/browser/trunk/RBRapier/RBRapier/Tools/Geometry/Analysis/TriangleMesh.py?rev=760

# original license:

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
##~ License
##~
##- The RuneBlade Foundation library is intended to ease some
##- aspects of writing intricate Jabber, XML, and User Interface (wxPython, etc.)
##- applications, while providing the flexibility to modularly change the
##- architecture. Enjoy.
##~
##~ Copyright (C) 2002  TechGame Networks, LLC.
##~
##~ This library is free software; you can redistribute it and/or
##~ modify it under the terms of the BSD style License as found in the
##~ LICENSE file included with this distribution.
##~
##~ TechGame Networks, LLC can be reached at:
##~ 3578 E. Hartsel Drive #211
##~ Colorado Springs, Colorado, USA, 80920
##~
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import operator # itemgetter


try:
    from weakref import WeakSet
except ImportError:
    # for py2k
    from weakref import ref
    class WeakSet(object):
        """Simple weak set implementation.

        >>> import gc
        >>> ws = WeakSet()
        >>> class Test(object):
        ...     pass
        >>> x = Test()
        >>> y = Test()
        >>> ws.add(x)
        >>> list(ws)[0] is x
        True
        >>> ws.add(y)
        >>> len(list(ws)) == 2
        True
        >>> del x
        >>> tmp = gc.collect()
        >>> list(ws)[0] is y
        True
        >>> del y
        >>> tmp = gc.collect()
        >>> list(ws)
        []
        """
        def __init__(self, data=None):
            self.data = set()
            def _remove(item, selfref=ref(self)):
                self = selfref()
                if self is not None:
                    self.data.discard(item)
            self._remove = _remove
            if data is not None:
                self.update(data)

        def __iter__(self):
            for itemref in self.data:
                item = itemref()
                if item is not None:
                    yield item

        def __len__(self):
            return sum(x() is not None for x in self.data)

        def __contains__(self, item):
            return ref(item) in self.data

        def __reduce__(self):
            return (self.__class__, (list(self),),
                    getattr(self, '__dict__', None))

        def add(self, item):
            self.data.add(ref(item, self._remove))

        def clear(self):
            self.data.clear()

        def copy(self):
            return self.__class__(self)

        def pop(self):
            while True:
                try:
                    itemref = self.data.pop()
                except KeyError:
                    raise KeyError('pop from empty WeakSet')
                item = itemref()
                if item is not None:
                    return item

        def remove(self, item):
            self.data.remove(ref(item))

        def discard(self, item):
            self.data.discard(ref(item))

        def update(self, other):
            if isinstance(other, self.__class__):
                self.data.update(other.data)
            else:
                for element in other:
                    self.add(element)
        def __ior__(self, other):
            self.update(other)
            return self

        # Helper functions for simple delegating methods.
        def _apply(self, other, method):
            if not isinstance(other, self.__class__):
                other = self.__class__(other)
            newdata = method(other.data)
            newset = self.__class__()
            newset.data = newdata
            return newset

        def difference(self, other):
            return self._apply(other, self.data.difference)
        __sub__ = difference

        def difference_update(self, other):
            if self is other:
                self.data.clear()
            else:
                self.data.difference_update(ref(item) for item in other)
        def __isub__(self, other):
            if self is other:
                self.data.clear()
            else:
                self.data.difference_update(ref(item) for item in other)
            return self

        def intersection(self, other):
            return self._apply(other, self.data.intersection)
        __and__ = intersection

        def intersection_update(self, other):
            self.data.intersection_update(ref(item) for item in other)
        def __iand__(self, other):
            self.data.intersection_update(ref(item) for item in other)
            return self

        def issubset(self, other):
            return self.data.issubset(ref(item) for item in other)
        __lt__ = issubset

        def __le__(self, other):
            return self.data <= set(ref(item) for item in other)

        def issuperset(self, other):
            return self.data.issuperset(ref(item) for item in other)
        __gt__ = issuperset

        def __ge__(self, other):
            return self.data >= set(ref(item) for item in other)

        def __eq__(self, other):
            if not isinstance(other, self.__class__):
                return NotImplemented
            return self.data == set(ref(item) for item in other)

        def symmetric_difference(self, other):
            return self._apply(other, self.data.symmetric_difference)
        __xor__ = symmetric_difference

        def symmetric_difference_update(self, other):
            if self is other:
                self.data.clear()
            else:
                self.data.symmetric_difference_update(ref(item) for item in other)
        def __ixor__(self, other):
            if self is other:
                self.data.clear()
            else:
                self.data.symmetric_difference_update(ref(item) for item in other)
            return self

        def union(self, other):
            return self._apply(other, self.data.union)
        __or__ = union

        def isdisjoint(self, other):
            return len(self.intersection(other)) == 0

class Edge:
    """A directed edge which keeps track of its faces."""

    def __init__(self, ev0, ev1):
        """Edge constructor.

        >>> edge = Edge(6, 9)
        >>> edge.verts
        (6, 9)
        >>> edge = Edge(8, 5)
        >>> edge.verts
        (8, 5)
        >>> edge = Edge(3, 3) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        """
        
        if ev0 == ev1:
            raise ValueError("Degenerate edge.")

        self.verts = (ev0, ev1)
        """Vertices of the edge."""

        self.faces = WeakSet()
        """Weak set of faces that have this edge."""

    def __repr__(self):
        """String representation.

        >>> Edge(1, 2)
        Edge(1, 2)
        """
        return "Edge(%s, %s)" % self.verts

class Face:
    """An oriented face which keeps track its adjacent faces."""

    def __init__(self, v0, v1, v2):
        """Construct face from vertices.

        >>> face = Face(3, 7, 5)
        >>> face.verts
        (3, 7, 5)
        >>> face = Face(9, 8, 2)
        >>> face.verts
        (2, 9, 8)
        >>> face = Face(6, 1, 4)
        >>> face.verts
        (1, 4, 6)
        >>> Face(30, 0, 30) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> Face(0, 40, 40) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> Face(50, 50, 0) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        >>> Face(7, 7, 7) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        """
        if v0 == v1 or v1 == v2 or v2 == v0:
            raise ValueError("Degenerate face.")
        if v0 < v1 and v0 < v2:
            self.verts = (v0, v1, v2)
        if v1 < v0 and v1 < v2:
            self.verts = (v1, v2, v0)
        if v2 < v0 and v2 < v1:
            self.verts = (v2, v0, v1)
        # no index yet
        self.index = None

        self.adjacent_faces = (WeakSet(), WeakSet(), WeakSet())
        """Weak sets of adjacent faces along edge opposite each vertex."""

    def __repr__(self):
        """String representation.

        >>> Face(3, 1, 2)
        Face(1, 2, 3)
        """
        return "Face(%s, %s, %s)" % self.verts

    def get_next_vertex(self, vi):
        """Get next vertex of face.

        >>> face = Face(8, 7, 5)
        >>> face.get_next_vertex(8)
        7
        >>> face.get_next_vertex(7)
        5
        >>> face.get_next_vertex(5)
        8
        >>> face.get_next_vertex(10) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        ValueError: ...
        """
        # XXX using list(self.verts) instead of self.verts
        # XXX for Python 2.5 compatibility
        return self.verts[(1, 2, 0)[list(self.verts).index(vi)]]

    def get_adjacent_faces(self, vi):
        """Get adjacent faces associated with the edge opposite a vertex."""
        # XXX using list(self.verts) instead of self.verts
        # XXX for Python 2.5 compatibility
        return self.adjacent_faces[list(self.verts).index(vi)]

class Mesh:
    """A mesh of interconnected faces.

    :ivar faces: List of faces of the mesh.
    :type faces: ``list`` of :class:`Face`"""
    def __init__(self, faces=None, lock=True):
        """Initialize a mesh, and optionally assign its faces and lock.

        :param faces: ``None``, or an iterator over faces to assign to
            the mesh.
        :type faces: ``Iterable`` or ``type(None)``
        :param lock: Whether to lock the mesh or not (ignored when
            `faces` are not specified).
        :type lock: ``bool``
        """
        self._faces = {}
        """Dictionary of all faces."""

        self._edges = {}
        """Dictionary of all edges."""

        if faces is not None:
            for v0, v1, v2 in faces:
                self.add_face(v0, v1, v2)
            if lock:
                self.lock()

    def __repr__(self):
        """String representation. Examples:

        >>> m = Mesh()
        >>> m
        Mesh()
        >>> tmp = m.add_face(1, 2, 3)
        >>> tmp = m.add_face(3, 2, 4)
        >>> m
        Mesh(faces=[(1, 2, 3), (2, 4, 3)], lock=False)
        >>> m.lock()
        >>> m
        Mesh(faces=[(1, 2, 3), (2, 4, 3)])
        >>> Mesh(faces=[(1, 2, 3),(3, 2, 4)])
        Mesh(faces=[(1, 2, 3), (2, 4, 3)])
        """
        try:
            self.faces
        except AttributeError:
            # unlocked
            if not self._faces:
                # special case
                return "Mesh()"
            return ("Mesh(faces=[%s], lock=False)"
                    % ', '.join(repr(faceverts)
                                for faceverts in sorted(self._faces)))
        else:
            # locked
            return ("Mesh(faces=[%s])"
                    % ', '.join(repr(face.verts)
                                for face in self.faces))

    def _add_edge(self, face, pv0, pv1):
        """Create new edge for mesh for given face, or return existing
        edge. Lists of faces of the new/existing edge is also updated,
        as well as lists of adjacent faces. For internal use only,
        called on each edge of the face in add_face.
        """
        # create edge if not found
        try:
            edge = self._edges[(pv0, pv1)]
        except KeyError:
            # create edge
            edge = Edge(pv0, pv1)
            self._edges[(pv0, pv1)] = edge

        # update edge's faces
        edge.faces.add(face)

        # find reverse edge in mesh
        try:
            otheredge = self._edges[(pv1, pv0)]
        except KeyError:
            pass
        else:
            # update adjacent faces
            pv2 = face.get_next_vertex(pv1)
            for otherface in otheredge.faces:
                otherpv2 = otherface.get_next_vertex(pv0)
                face.get_adjacent_faces(pv2).add(otherface)
                otherface.get_adjacent_faces(otherpv2).add(face)

    def add_face(self, v0, v1, v2):
        """Create new face for mesh, or return existing face. List of
        adjacent faces is also updated.

        >>> m = Mesh()
        >>> f0 = m.add_face(0, 1, 2)
        >>> [list(faces) for faces in f0.adjacent_faces]
        [[], [], []]

        >>> m = Mesh()
        >>> f0 = m.add_face(0, 1, 2)
        >>> f1 = m.add_face(2, 1, 3)
        >>> f2 = m.add_face(2, 3, 4)
        >>> len(m._faces)
        3
        >>> len(m._edges)
        9
        >>> f3 = m.add_face(2, 3, 4)
        >>> f3 is f2
        True
        >>> f4 = m.add_face(10, 11, 12)
        >>> f5 = m.add_face(12, 10, 11)
        >>> f6 = m.add_face(11, 12, 10)
        >>> f4 is f5
        True
        >>> f4 is f6
        True
        >>> len(m._faces)
        4
        >>> len(m._edges)
        12

        Another mesh::

            0->-1
             \\ / \\
              2-<-3
              2->-3
               \\ /
                4

        >>> m = Mesh()
        >>> f0 = m.add_face(0, 1, 2)
        >>> f1 = m.add_face(1, 3, 2)
        >>> f2 = m.add_face(2, 3, 4)
        >>> list(f0.get_adjacent_faces(0))
        [Face(1, 3, 2)]
        >>> list(f0.get_adjacent_faces(1))
        []
        >>> list(f0.get_adjacent_faces(2))
        []
        >>> list(f1.get_adjacent_faces(1))
        [Face(2, 3, 4)]
        >>> list(f1.get_adjacent_faces(3))
        [Face(0, 1, 2)]
        >>> list(f1.get_adjacent_faces(2))
        []
        >>> list(f2.get_adjacent_faces(2))
        []
        >>> list(f2.get_adjacent_faces(3))
        []
        >>> list(f2.get_adjacent_faces(4))
        [Face(1, 3, 2)]
        >>> # add an extra face, and check changes
        >>> f3 = m.add_face(2, 3, 5)
        >>> list(f0.get_adjacent_faces(0))
        [Face(1, 3, 2)]
        >>> list(f0.get_adjacent_faces(1))
        []
        >>> list(f0.get_adjacent_faces(2))
        []
        >>> list(f1.get_adjacent_faces(1)) # extra face here!
        [Face(2, 3, 4), Face(2, 3, 5)]
        >>> list(f1.get_adjacent_faces(3))
        [Face(0, 1, 2)]
        >>> list(f1.get_adjacent_faces(2))
        []
        >>> list(f2.get_adjacent_faces(2))
        []
        >>> list(f2.get_adjacent_faces(3))
        []
        >>> list(f2.get_adjacent_faces(4))
        [Face(1, 3, 2)]
        """
        face = Face(v0, v1, v2)
        try:
            face = self._faces[face.verts]
        except KeyError:
            # create edges and update links between faces
            self._add_edge(face, v0, v1)
            self._add_edge(face, v1, v2)
            self._add_edge(face, v2, v0)
            # register face in mesh
            self._faces[face.verts] = face

        return face

    def lock(self):
        """Lock the mesh. Frees memory by clearing the structures
        which are only used to update the face adjacency lists. Sets
        the faces attribute to the sorted list of all faces (sorting helps
        with ensuring that the strips in faces are close together).

        >>> m = Mesh()
        >>> f0 = m.add_face(3, 1, 2)
        >>> f1 = m.add_face(0, 1, 2)
        >>> f2 = m.add_face(5, 6, 2)
        >>> m.faces # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: ...
        >>> m.lock()
        >>> m.faces # should be sorted
        [Face(0, 1, 2), Face(1, 2, 3), Face(2, 5, 6)]
        >>> m.faces[0].index
        0
        >>> m.faces[1].index
        1
        >>> m.faces[2].index
        2
        >>> m._faces # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: ...
        >>> m._edges # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: ...
        >>> m.add_face(1, 2, 3) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        AttributeError: ...
        """
        # store faces and set their index
        self.faces = []
        for i, (verts, face) in enumerate(sorted(self._faces.iteritems(),
                                          key=operator.itemgetter(0))):
            face.index = i
            self.faces.append(face)
        # remove helper structures
        del self._faces
        del self._edges

    def discard_face(self, face):
        """Remove the face from the mesh.

        >>> m = Mesh()
        >>> f0 = m.add_face(0, 1, 2)
        >>> f1 = m.add_face(1, 3, 2)
        >>> f2 = m.add_face(2, 3, 4)
        >>> m.lock()
        >>> list(f0.get_adjacent_faces(0))
        [Face(1, 3, 2)]
        >>> m.discard_face(f1)
        >>> list(f0.get_adjacent_faces(0))
        []
        """
        # note: don't delete, but set to None, to ensure that other
        # face indices remain valid
        self.faces[face.index] = None
        for adj_faces in face.adjacent_faces:
            for adj_face in adj_faces:
                for adj_adj_faces in adj_face.adjacent_faces:
                    adj_adj_faces.discard(face)
                    # faster (but breaks py3k!!):
                    #if id(face) in adj_adj_faces.data:
                    #    del adj_adj_faces.data[id(face)]

if __name__=='__main__':
    import doctest
    doctest.testmod()
