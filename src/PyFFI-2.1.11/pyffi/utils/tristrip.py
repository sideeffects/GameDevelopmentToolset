"""A wrapper for TriangleStripifier and some utility functions, for
stripification of sets of triangles, stitching and unstitching strips,
and triangulation of strips."""

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

try:
    import pytristrip
except ImportError:
    pytristrip = None
    from pyffi.utils.trianglestripifier import TriangleStripifier
    from pyffi.utils.trianglemesh import Mesh

def triangulate(strips):
    """A generator for iterating over the faces in a set of
    strips. Degenerate triangles in strips are discarded.

    >>> triangulate([[1, 0, 1, 2, 3, 4, 5, 6]])
    [(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5), (4, 6, 5)]
    """

    triangles = []

    for strip in strips:
        if len(strip) < 3: continue # skip empty strips
        i = strip.__iter__()
        j = False
        t1, t2 = i.next(), i.next()
        for k in xrange(2, len(strip)):
            j = not j
            t0, t1, t2 = t1, t2, i.next()
            if t0 == t1 or t1 == t2 or t2 == t0: continue
            triangles.append((t0, t1, t2) if j else (t0, t2, t1))

    return triangles

def _generate_faces_from_triangles(triangles):
    i = triangles.__iter__()
    while True:
        yield (i.next(), i.next(), i.next())

def _sort_triangle_indices(triangles):
    """Sorts indices of each triangle so lowest index always comes first.
    Also removes degenerate triangles.

    >>> list(_sort_triangle_indices([(2,1,3),(0,2,6),(9,8,4)]))
    [(1, 3, 2), (0, 2, 6), (4, 9, 8)]
    >>> list(_sort_triangle_indices([(2,1,1),(0,2,6),(9,8,4)]))
    [(0, 2, 6), (4, 9, 8)]
    """
    for t0, t1, t2 in triangles:
        # skip degenerate triangles
        if t0 == t1 or t1 == t2 or t2 == t0:
            continue
        # sort indices
        if t0 < t1 and t0 < t2:
            yield (t0, t1, t2)
        elif t1 < t0 and t1 < t2:
            yield (t1, t2, t0)
        elif t2 < t0 and t2 < t1:
            yield (t2, t0, t1)
        else:
            # should *never* happen
            raise RuntimeError(
                "Unexpected error while sorting triangle indices.")

def _check_strips(triangles, strips):
    """Checks that triangles and strips describe the same geometry.

    >>> _check_strips([(0,1,2),(2,1,3)], [[0,1,2,3]])
    >>> _check_strips([(0,1,2),(2,1,3)], [[3,2,1,0]])
    >>> _check_strips([(0,1,2),(2,1,3)], [[3,2,1,0,1]])
    >>> _check_strips([(0,1,2),(2,1,3)], [[3,3,3,2,1,0,1]])
    >>> _check_strips([(0,1,2),(2,1,3),(1,0,1)], [[0,1,2,3]])
    >>> _check_strips([(0,1,2),(2,1,3),(4,4,4)], [[0,1,2,3]])
    >>> _check_strips([(0,1,2),(2,1,3)], [[0,1,2,3], [2,3,4]]) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> _check_strips([(0,1,2),(2,1,3),(2,3,4)], [[0,1,2,3]]) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> _check_strips([(0,1,2),(2,1,3),(2,3,4),(3,8,1)], [[0,1,2,3,7],[9,10,5,9]]) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    """
    # triangulate
    strips_triangles = set(_sort_triangle_indices(triangulate(strips)))
    triangles = set(_sort_triangle_indices(triangles))
    # compare
    if strips_triangles != triangles:
        raise ValueError(
            "triangles and strips do not match\n"
            "triangles = %s\n"
            "strips = %s\n"
            "triangles - strips = %s\n"
            "strips - triangles = %s\n"
            % (triangles, strips,
               triangles - strips_triangles,
               strips_triangles - triangles))

def stripify(triangles, stitchstrips = False):
    """Converts triangles into a list of strips.

    If stitchstrips is True, then everything is wrapped in a single strip using
    degenerate triangles.

    >>> triangles = [(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips)
    >>> triangles = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11), (12, 13, 14), (15, 16, 17), (18, 19, 20), (21, 22, 23)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips)
    >>> triangles = [(0, 1, 2), (0, 1, 2)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips)
    >>> triangles = [(0, 1, 2), (2, 1, 0)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips)
    >>> triangles = [(0, 1, 2), (2, 1, 0), (1, 2, 3)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips) # NvTriStrip gives wrong result
    >>> triangles = [(0, 1, 2), (0, 1, 3)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips) # NvTriStrip gives wrong result
    >>> triangles = [(1, 5, 2), (5, 2, 6), (5, 9, 6), (9, 6, 10), (9, 13, 10), (13, 10, 14), (0, 4, 1), (4, 1, 5), (4, 8, 5), (8, 5, 9), (8, 12, 9), (12, 9, 13), (2, 6, 3), (6, 3, 7), (6, 10, 7), (10, 7, 11), (10, 14, 11), (14, 11, 15)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips) # NvTriStrip gives wrong result
    >>> triangles = [(1, 2, 3), (4, 5, 6), (6, 5, 7), (8, 5, 9), (4, 10, 9), (8, 3, 11), (8, 10, 3), (12, 13, 6), (14, 2, 15), (16, 13, 15), (16, 2, 3), (3, 2, 1)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips) # detects bug reported by PacificMorrowind
    >>> triangles = [(354, 355, 356), (355, 356, 354), (354, 355, 356), (355, 356, 354), (354, 355, 356), (356, 354, 355), (354, 355, 356), (357, 359, 358),
    ...              (380, 372, 381), (372, 370, 381), (381, 370, 354), (370, 367, 354), (367, 366, 354), (366, 355, 354), (355, 356, 354), (354, 356, 381),
    ...              (356, 355, 357), (357, 356, 355), (356, 355, 357), (356, 355, 357), (357, 356, 355)]
    >>> strips = stripify(triangles)
    >>> _check_strips(triangles, strips) # NvTriStrip gives wrong result
    """

    if pytristrip:
        strips = pytristrip.stripify(triangles)
    else:
        strips = []
        # build a mesh from triangles
        mesh = Mesh()
        for face in triangles:
            try:
                mesh.add_face(*face)
            except ValueError:
                # degenerate face
                pass
        mesh.lock()

        # calculate the strip
        stripifier = TriangleStripifier(mesh)
        strips = stripifier.find_all_strips()

    # stitch the strips if needed
    if stitchstrips:
        return [stitch_strips(strips)]
    else:
        return strips

class OrientedStrip:
    """An oriented strip, with stitching support."""

    def __init__(self, strip):
        """Construct oriented strip from regular strip (i.e. a list).

        Constructors
        ------------

        >>> ostrip = OrientedStrip([0,1,2,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        False

        >>> ostrip = OrientedStrip([0,0,1,2,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        True
        >>> ostrip2 = OrientedStrip(ostrip)
        >>> ostrip2.vertices
        [0, 1, 2, 3]
        >>> ostrip2.reversed
        True

        >>> ostrip = OrientedStrip(None) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeError: ...

        Compactify
        ----------

        >>> ostrip = OrientedStrip([0,0,0,1,2,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        False
        >>> ostrip = OrientedStrip([0,0,0,0,1,2,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        True
        >>> ostrip = OrientedStrip([0,0,0,1,2,3,3,3,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        False
        >>> ostrip = OrientedStrip([0,0,0,0,1,2,3,3,3,3])
        >>> ostrip.vertices
        [0, 1, 2, 3]
        >>> ostrip.reversed
        True
        """

        if isinstance(strip, (list, tuple)):
            # construct from strip
            self.vertices = list(strip)
            self.reversed = False
            self.compactify()
        elif isinstance(strip, OrientedStrip):
            # copy constructor
            self.vertices = strip.vertices[:]
            self.reversed = strip.reversed
        else:
            raise TypeError(
                "expected list or OrientedStrip, but got %s"
                % strip.__class__.__name__)

    def compactify(self):
        """Remove degenerate faces from front and back."""
        # remove from front
        if len(self.vertices) < 3:
            raise ValueError(
                "strip must have at least one non-degenerate face")
        while self.vertices[0] == self.vertices[1]:
            del self.vertices[0]
            self.reversed = not self.reversed
            if len(self.vertices) < 3:
                raise ValueError(
                    "strip must have at least one non-degenerate face")
        # remove from back
        while self.vertices[-1] == self.vertices[-2]:
            del self.vertices[-1]
            if len(self.vertices) < 3:
                raise ValueError(
                    "strip must have at least one non-degenerate face")

    def reverse(self):
        """Reverse vertices."""
        self.vertices.reverse()
        if len(self.vertices) & 1:
            self.reversed = not self.reversed

    def __len__(self):
        if self.reversed:
            return len(self.vertices) + 1
        else:
            return len(self.vertices)

    def __iter__(self):
        if self.reversed:
            yield self.vertices[0]
        for vert in self.vertices:
            yield vert

    def __str__(self):
        """String representation.

        >>> print(OrientedStrip([0, 1, 2, 3, 4]))
        [0, 1, 2, 3, 4]
        >>> print(OrientedStrip([0, 0, 1, 2, 3, 4]))
        [0, 0, 1, 2, 3, 4]
        """
        return str(list(self))

    def __repr__(self):
        return "OrientedStrip(%s)" % str(list(self))

    def get_num_stitches(self, other):
        """Get number of stitches required to glue the vertices of self to
        other.
        """
        # do last vertex of self and first vertex of other match?
        has_common_vertex = (self.vertices[-1] == other.vertices[0])

        # do windings match?
        if len(self.vertices) & 1:
            has_winding_match = (self.reversed != other.reversed)
        else:
            has_winding_match = (self.reversed == other.reversed)

        # append stitches
        if has_common_vertex:
            if has_winding_match:
                return 0
            else:
                return 1
        else:
            if has_winding_match:
                return 2
            else:
                return 3

    def __add__(self, other):
        """Combine two strips, using minimal number of stitches.

        >>> # stitch length 0 code path
        >>> OrientedStrip([0,1,2,3]) + OrientedStrip([3,4,5])
        OrientedStrip([0, 1, 2, 3, 3, 4, 5])
        >>> OrientedStrip([0,1,2]) + OrientedStrip([2,2,3,4])
        OrientedStrip([0, 1, 2, 2, 3, 4])

        >>> # stitch length 1 code path
        >>> OrientedStrip([0,1,2]) + OrientedStrip([2,3,4])
        OrientedStrip([0, 1, 2, 2, 2, 3, 4])
        >>> OrientedStrip([0,1,2,3]) + OrientedStrip([3,3,4,5])
        OrientedStrip([0, 1, 2, 3, 3, 3, 4, 5])

        >>> # stitch length 2 code path
        >>> OrientedStrip([0,1,2,3]) + OrientedStrip([7,8,9])
        OrientedStrip([0, 1, 2, 3, 3, 7, 7, 8, 9])
        >>> OrientedStrip([0,1,2]) + OrientedStrip([7,7,8,9])
        OrientedStrip([0, 1, 2, 2, 7, 7, 8, 9])

        >>> # stitch length 3 code path
        >>> OrientedStrip([0,1,2,3]) + OrientedStrip([7,7,8,9])
        OrientedStrip([0, 1, 2, 3, 3, 7, 7, 7, 8, 9])
        >>> OrientedStrip([0,1,2]) + OrientedStrip([7,8,9])
        OrientedStrip([0, 1, 2, 2, 7, 7, 7, 8, 9])
        """
        # make copy of self
        result = OrientedStrip(self)

        # get number of stitches required
        num_stitches = self.get_num_stitches(other)
        if num_stitches >= 4 or num_stitches < 0:
            # should *never* happen
            raise RuntimeError("Unexpected error during stitching.")

        # append stitches
        if num_stitches >= 1:
            result.vertices.append(self.vertices[-1]) # first stitch
        if num_stitches >= 2:
            result.vertices.append(other.vertices[0]) # second stitch
        if num_stitches >= 3:
            result.vertices.append(other.vertices[0]) # third stitch

        # append other vertices
        result.vertices.extend(other.vertices)

        return result

def stitch_strips(strips):
    """Stitch strips keeping stitch size minimal.

    >>> # stitch length 0 code path
    >>> stitch_strips([[3,4,5],[0,1,2,3]])
    [0, 1, 2, 3, 3, 4, 5]
    >>> stitch_strips([[2,2,3,4],[0,1,2]])
    [0, 1, 2, 2, 3, 4]

    >>> # check result when changing ordering of strips
    >>> stitch_strips([[0,1,2,3],[3,4,5]])
    [0, 1, 2, 3, 3, 4, 5]

    >>> # check result when changing direction of strips
    >>> stitch_strips([[3,2,1,0],[3,4,5]])
    [0, 1, 2, 3, 3, 4, 5]

    >>> # stitch length 1 code path
    >>> stitch_strips([[2,3,4],[0,1,2]])
    [0, 1, 2, 2, 2, 3, 4]
    >>> stitch_strips([[3,3,4,5],[0,1,2,3]])
    [0, 1, 2, 3, 3, 3, 4, 5]

    >>> # stitch length 2 code path
    >>> stitch_strips([[7,8,9],[0,1,2,3]])
    [0, 1, 2, 3, 3, 7, 7, 8, 9]
    >>> stitch_strips([[7,7,8,9],[0,1,2]])
    [0, 1, 2, 2, 7, 7, 8, 9]

    >>> # stitch length 3 code path... but algorithm reverses strips so
    >>> # only 2 stitches are needed (compare with OrientedStrip doctest)
    >>> stitch_strips([[7,7,8,9],[0,1,2,3]])
    [3, 2, 1, 0, 0, 9, 9, 8, 7]
    >>> stitch_strips([[7,8,9],[0,1,2]])
    [0, 1, 2, 2, 9, 9, 8, 7]
    """

    class ExperimentSelector:
        """Helper class to select best experiment."""
        def __init__(self):
            self.best_ostrip1 = None
            self.best_ostrip2 = None
            self.best_num_stitches = None
            self.best_ostrip_index = None

        def update(self, ostrip_index, ostrip1, ostrip2):
            num_stitches = ostrip1.get_num_stitches(ostrip2)
            if ((self.best_num_stitches is None)
                or (num_stitches < self.best_num_stitches)):
                self.best_ostrip1 = ostrip1
                self.best_ostrip2 = ostrip2
                self.best_ostrip_index = ostrip_index
                self.best_num_stitches = num_stitches

    # get all strips and their orientation, and their reverse
    ostrips = [(OrientedStrip(strip), OrientedStrip(strip))
               for strip in strips if len(strip) >= 3]
    for ostrip, reversed_ostrip in ostrips:
        reversed_ostrip.reverse()
    # start with one of the strips
    if not ostrips:
        # no strips!
        return []
    result = ostrips.pop()[0]
    # go on as long as there are strips left to process
    while ostrips:
        selector = ExperimentSelector()

        for ostrip_index, (ostrip, reversed_ostrip) in enumerate(ostrips):
            # try various ways of stitching strips
            selector.update(ostrip_index, result, ostrip)
            selector.update(ostrip_index, ostrip, result)
            selector.update(ostrip_index, result, reversed_ostrip)
            selector.update(ostrip_index, reversed_ostrip, result)
            # break early if global optimum is already reached
            if selector.best_num_stitches == 0:
                break
        # get best result, perform the actual stitching, and remove
        # strip from ostrips
        result = selector.best_ostrip1 + selector.best_ostrip2
        ostrips.pop(selector.best_ostrip_index)
    # get strip
    strip = list(result)
    # check if we can remove first vertex by reversing strip
    if strip[0] == strip[1] and (len(strip) & 1 == 0):
        strip = strip[1:]
        strip.reverse()
    # return resulting strip
    return strip

def unstitch_strip(strip):
    """Revert stitched strip back to a set of strips without stitches.

    >>> strip = [0,1,2,2,3,3,4,5,6,7,8]
    >>> triangles = triangulate([strip])
    >>> strips = unstitch_strip(strip)
    >>> _check_strips(triangles, strips)
    >>> strips
    [[0, 1, 2], [3, 3, 4, 5, 6, 7, 8]]
    >>> strip = [0,1,2,3,3,4,4,4,5,6,7,8]
    >>> triangles = triangulate([strip])
    >>> strips = unstitch_strip(strip)
    >>> _check_strips(triangles, strips)
    >>> strips
    [[0, 1, 2, 3], [4, 4, 5, 6, 7, 8]]
    >>> strip = [0,1,2,3,4,4,4,4,5,6,7,8]
    >>> triangles = triangulate([strip])
    >>> strips = unstitch_strip(strip)
    >>> _check_strips(triangles, strips)
    >>> strips
    [[0, 1, 2, 3, 4], [4, 4, 5, 6, 7, 8]]
    >>> strip = [0,1,2,3,4,4,4,4,4,5,6,7,8]
    >>> triangles = triangulate([strip])
    >>> strips = unstitch_strip(strip)
    >>> _check_strips(triangles, strips)
    >>> strips
    [[0, 1, 2, 3, 4], [4, 5, 6, 7, 8]]
    >>> strip = [0,0,1,1,2,2,3,3,4,4,4,4,4,5,5,6,6,7,7,8,8]
    >>> triangles = triangulate([strip])
    >>> strips = unstitch_strip(strip)
    >>> _check_strips(triangles, strips)
    >>> strips
    []"""
    strips = []
    currentstrip = []
    i = 0
    while i < len(strip)-1:
        winding = i & 1
        currentstrip.append(strip[i])
        if strip[i] == strip[i+1]:
            # stitch detected, add current strip to list of strips
            strips.append(currentstrip)
            # and start a new one, taking into account winding
            if winding == 1:
                currentstrip = []
            else:
                currentstrip = [strip[i+1]]
        i += 1
    # add last part
    currentstrip.extend(strip[i:])
    strips.append(currentstrip)
    # sanitize strips
    for strip in strips:
        while len(strip) >= 3 and strip[0] == strip[1] == strip[2]:
            strip.pop(0)
            strip.pop(0)
    return [strip for strip in strips if len(strip) > 3 or (len(strip) == 3 and strip[0] != strip[1])]

if __name__=='__main__':
    import doctest
    doctest.testmod()
