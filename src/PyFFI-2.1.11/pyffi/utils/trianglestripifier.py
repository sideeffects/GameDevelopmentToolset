"""A general purpose stripifier, based on NvTriStrip (http://developer.nvidia.com/)

Credit for porting NvTriStrip to Python goes to the RuneBlade Foundation
library:
http://techgame.net/projects/Runeblade/browser/trunk/RBRapier/RBRapier/Tools/Geometry/Analysis/TriangleStripifier.py?rev=760

The algorithm of this stripifier is an improved version of the RuneBlade
Foundation / NVidia stripifier; it makes no assumptions about the
underlying geometry whatsoever and is intended to produce valid
output in all circumstances.
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

import itertools
import random # choice

from pyffi.utils.trianglemesh import Face, Mesh

class TriangleStrip(object):
    """A heavily specialized oriented strip of faces.

    Heavily adapted from NvTriStrip and RuneBlade. Originals can be found at
    http://developer.nvidia.com/view.asp?IO=nvtristrip_library
    and
    http://techgame.net/projects/Runeblade/browser/trunk/RBRapier/RBRapier/Tools/Geometry/Analysis/TriangleStripifier.py?rev=760
    """

    def __init__(self, stripped_faces=None,
                 faces=None, vertices=None, reversed_=False):
        """Initialise the triangle strip."""
        self.faces = faces if faces is not None else []
        self.vertices = vertices if vertices is not None else []
        self.reversed_ = reversed_

        # set of indices of stripped faces
        self.stripped_faces = (stripped_faces
                               if stripped_faces is not None else set())

    def __repr__(self):
        return ("TriangleStrip(stripped_faces=%s, faces=%s, vertices=%s, reversed_=%s)"
                % (repr(self.stripped_faces), repr(self.faces),
                   repr(self.vertices), repr(self.reversed_)))

    def get_unstripped_adjacent_face(self, face, vi):
        """Get adjacent face which is not yet stripped."""
        for otherface in face.get_adjacent_faces(vi):
            if otherface.index not in self.stripped_faces:
                return otherface

    def traverse_faces(self, start_vertex, start_face, forward):
        """Builds a strip traveral of faces starting from the
        start_face and the edge opposite start_vertex. Returns number
        of faces added.
        """
        count = 0
        pv0 = start_vertex
        pv1 = start_face.get_next_vertex(pv0)
        pv2 = start_face.get_next_vertex(pv1)
        next_face = self.get_unstripped_adjacent_face(start_face, pv0)
        while next_face:
            self.stripped_faces.add(next_face.index)
            count += 1
            if count & 1:
                if forward:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    self.vertices.append(pv1)
                    self.faces.append(next_face)
                else:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    self.vertices.insert(0, pv2)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_
            else:
                if forward:
                    pv0 = pv2
                    pv2 = next_face.get_next_vertex(pv1)
                    self.vertices.append(pv2)
                    self.faces.append(next_face)
                else:
                    pv0 = pv1
                    pv1 = next_face.get_next_vertex(pv0)
                    self.vertices.insert(0, pv1)
                    self.faces.insert(0, next_face)
                    self.reversed_ = not self.reversed_
            next_face = self.get_unstripped_adjacent_face(next_face, pv0)
        return count

    def build(self, start_vertex, start_face):
        """Builds the face strip forwards, then backwards. Returns
        index of start_face.

        Check case of single triangle
        -----------------------------

        >>> m = Mesh()
        >>> face = m.add_face(0, 1, 2)
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(0, face)
        0
        >>> t
        TriangleStrip(stripped_faces=set([0]), faces=[Face(0, 1, 2)], vertices=[0, 1, 2], reversed_=False)
        >>> t.get_strip()
        [0, 1, 2]
        >>> t = TriangleStrip()
        >>> t.build(1, face)
        0
        >>> t
        TriangleStrip(stripped_faces=set([0]), faces=[Face(0, 1, 2)], vertices=[1, 2, 0], reversed_=False)
        >>> t.get_strip()
        [1, 2, 0]
        >>> t = TriangleStrip()
        >>> t.build(2, face)
        0
        >>> t
        TriangleStrip(stripped_faces=set([0]), faces=[Face(0, 1, 2)], vertices=[2, 0, 1], reversed_=False)
        >>> t.get_strip()
        [2, 0, 1]

        Check case of two triangles, with special strip winding fix
        -----------------------------------------------------------

        >>> m = Mesh()
        >>> face0 = m.add_face(0, 1, 2)
        >>> face1 = m.add_face(2, 1, 3)
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(0, face0)
        0
        >>> t
        TriangleStrip(stripped_faces=set([0, 1]), faces=[Face(0, 1, 2), Face(1, 3, 2)], vertices=[0, 1, 2, 3], reversed_=False)
        >>> t.get_strip()
        [0, 1, 2, 3]
        >>> t = TriangleStrip()
        >>> t.build(1, face0)
        1
        >>> t
        TriangleStrip(stripped_faces=set([0, 1]), faces=[Face(1, 3, 2), Face(0, 1, 2)], vertices=[3, 1, 2, 0], reversed_=True)
        >>> t.get_strip()
        [3, 2, 1, 0]
        >>> t = TriangleStrip()
        >>> t.build(2, face1)
        1
        >>> t
        TriangleStrip(stripped_faces=set([0, 1]), faces=[Face(0, 1, 2), Face(1, 3, 2)], vertices=[0, 2, 1, 3], reversed_=True)
        >>> t.get_strip()
        [0, 1, 2, 3]
        >>> t = TriangleStrip()
        >>> t.build(3, face1)
        0
        >>> t
        TriangleStrip(stripped_faces=set([0, 1]), faces=[Face(1, 3, 2), Face(0, 1, 2)], vertices=[3, 2, 1, 0], reversed_=False)
        >>> t.get_strip()
        [3, 2, 1, 0]

        Check that extra vertex is appended to fix winding
        --------------------------------------------------

        >>> m = Mesh()
        >>> face0 = m.add_face(1, 3, 2)
        >>> face1 = m.add_face(2, 3, 4)
        >>> face2 = m.add_face(4, 3, 5)
        >>> face3 = m.add_face(4, 5, 6)
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(2, face1)
        1
        >>> t
        TriangleStrip(stripped_faces=set([0, 1, 2, 3]), faces=[Face(1, 3, 2), Face(2, 3, 4), Face(3, 5, 4), Face(4, 5, 6)], vertices=[1, 2, 3, 4, 5, 6], reversed_=True)
        >>> t.get_strip()
        [1, 1, 2, 3, 4, 5, 6]

        Check that strip is reversed to fix winding
        -------------------------------------------

        >>> m = Mesh()
        >>> face0 = m.add_face(1, 3, 2)
        >>> face1 = m.add_face(2, 3, 4)
        >>> face2 = m.add_face(4, 3, 5)
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(2, face1)
        1
        >>> t
        TriangleStrip(stripped_faces=set([0, 1, 2]), faces=[Face(1, 3, 2), Face(2, 3, 4), Face(3, 5, 4)], vertices=[1, 2, 3, 4, 5], reversed_=True)
        >>> t.get_strip()
        [5, 4, 3, 2, 1]

        More complicated mesh
        ---------------------

        >>> m = Mesh()
        >>> face0 = m.add_face(0, 1, 2)
        >>> face1 = m.add_face(2, 1, 7)
        >>> face2 = m.add_face(2, 7, 4)
        >>> face3 = m.add_face(5, 3, 2)
        >>> face4 = m.add_face(2, 1, 9)
        >>> face5 = m.add_face(4, 7, 10)
        >>> face6 = m.add_face(4, 10, 11)
        >>> face7 = m.add_face(11, 10, 12)
        >>> face8 = m.add_face(1, 0, 13)
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(7, face1)
        4
        >>> t.faces[4] == face1 # check result from build
        True
        >>> t.stripped_faces
        set([0, 1, 2, 5, 6, 7, 8])
        >>> t.faces
        [Face(10, 12, 11), Face(4, 10, 11), Face(4, 7, 10), Face(2, 7, 4), Face(1, 7, 2), Face(0, 1, 2), Face(0, 13, 1)]
        >>> t.vertices
        [12, 11, 10, 4, 7, 2, 1, 0, 13]
        >>> t.reversed_
        False
        >>> t.get_strip()
        [12, 11, 10, 4, 7, 2, 1, 0, 13]

        Mesh which has more than a single strip
        ---------------------------------------

        >>> m = Mesh()
        >>> tmp = m.add_face(2, 1, 7) # in strip
        >>> start_face = m.add_face(0, 1, 2) # in strip
        >>> tmp = m.add_face(2, 7, 4) # in strip
        >>> tmp = m.add_face(4, 7, 11) # in strip
        >>> tmp = m.add_face(5, 3, 2)
        >>> tmp = m.add_face(1, 0, 8) # in strip
        >>> tmp = m.add_face(0, 8, 9) # bad orientation!
        >>> tmp = m.add_face(8, 0, 10) # in strip
        >>> m.lock()
        >>> t = TriangleStrip()
        >>> t.build(0, start_face)
        2
        >>> t.vertices
        [10, 8, 0, 1, 2, 7, 4, 11]
        >>> t.get_strip()
        [10, 8, 0, 1, 2, 7, 4, 11]
        """
        del self.faces[:]
        del self.vertices[:]
        self.reversed_ = False
        v0 = start_vertex
        v1 = start_face.get_next_vertex(v0)
        v2 = start_face.get_next_vertex(v1)
        self.stripped_faces.add(start_face.index)
        self.faces.append(start_face)
        self.vertices.append(v0)
        self.vertices.append(v1)
        self.vertices.append(v2)
        self.traverse_faces(v0, start_face, True)
        return self.traverse_faces(v2, start_face, False)

    def get_strip(self):
        """Get strip in forward winding."""
        strip = []
        if self.reversed_:
            if len(self.vertices) & 1:
                strip = list(reversed(self.vertices))
            elif len(self.vertices) == 4:
                strip = list(self.vertices[i] for i in (0, 2, 1, 3))
            else:
                strip = list(self.vertices)
                strip.insert(0, strip[0])
        else:
            strip = list(self.vertices)
        return strip

class Experiment(object):
    """A stripification experiment, essentially consisting of a set of
    adjacent strips.
    """

    def __init__(self, start_vertex, start_face):
        self.stripped_faces = set()
        self.start_vertex = start_vertex
        self.start_face = start_face
        self.strips = []

    def build(self):
        """Build strips, starting from start_vertex and start_face.

        >>> m = Mesh()
        >>> tmp = m.add_face(2, 1, 7)
        >>> s1_face = m.add_face(0, 1, 2)
        >>> tmp = m.add_face(2, 7, 4) # in strip
        >>> tmp = m.add_face(4, 7, 11) # in strip
        >>> tmp = m.add_face(5, 3, 2)
        >>> tmp = m.add_face(1, 0, 8) # in strip
        >>> tmp = m.add_face(0, 8, 9) # bad orientation!
        >>> tmp = m.add_face(8, 0, 10) # in strip
        >>> tmp = m.add_face(10, 11, 8) # in strip
        >>> # parallel strip
        >>> s2_face = m.add_face(0, 2, 21) # in strip
        >>> tmp = m.add_face(21, 2, 22) # in strip
        >>> tmp = m.add_face(2, 4, 22) # in strip
        >>> tmp = m.add_face(21, 24, 0) # in strip
        >>> tmp = m.add_face(9, 0, 24) # in strip
        >>> # parallel strip, further down
        >>> s3_face = m.add_face(8, 11, 31) # in strip
        >>> tmp = m.add_face(8, 31, 32) # in strip
        >>> tmp = m.add_face(31, 11, 33) # in strip
        >>> m.lock()
        >>> # build experiment
        >>> exp = Experiment(0, s1_face)
        >>> exp.build()
        >>> len(exp.strips)
        2
        >>> exp.strips[0].get_strip()
        [11, 4, 7, 2, 1, 0, 8, 10, 11]
        >>> exp.strips[1].get_strip()
        [4, 22, 2, 21, 0, 24, 9]
        >>> # note: with current algorithm [32, 8, 31, 11, 33] is not found
        """
        # build initial strip
        strip = TriangleStrip(stripped_faces=self.stripped_faces)
        strip.build(self.start_vertex, self.start_face)
        self.strips.append(strip)
        # build adjacent strips
        num_faces = len(strip.faces)
        if num_faces >= 4:
            face_index = num_faces >> 1 # quick / 2
            self.build_adjacent(strip, face_index)
            self.build_adjacent(strip, face_index + 1)
        elif num_faces == 3:
            if not self.build_adjacent(strip, 0):
                self.build_adjacent(strip, 2)
            self.build_adjacent(strip, 1)
        elif num_faces == 2:
            self.build_adjacent(strip, 0)
            self.build_adjacent(strip, 1)
        elif num_faces == 1:
            self.build_adjacent(strip, 0)

    def build_adjacent(self, strip, face_index):
        """Build strips adjacent to given strip, and add them to the
        experiment. This is a helper function used by build.
        """
        opposite_vertex = strip.vertices[face_index + 1]
        face = strip.faces[face_index]
        other_face = strip.get_unstripped_adjacent_face(face, opposite_vertex)
        if other_face:
            winding = strip.reversed_
            if face_index & 1:
                winding = not winding
            other_strip = TriangleStrip(stripped_faces=self.stripped_faces)
            if winding:
                other_vertex = strip.vertices[face_index]
                face_index = other_strip.build(other_vertex, other_face)
            else:
                other_vertex = strip.vertices[face_index + 2]
                face_index = other_strip.build(other_vertex, other_face)
            self.strips.append(other_strip)
            if face_index > (len(other_strip.faces) >> 1): # quick / 2
                self.build_adjacent(other_strip, face_index - 1)
            elif face_index < len(other_strip.faces) - 1:
                self.build_adjacent(other_strip, face_index + 1)
            return True
        return False

class ExperimentSelector(object):

    def __init__(self):
        self.best_score = -1.0
        self.best_experiment = None

    def update(self, experiment):
        """Updates best experiment with given experiment, if given
        experiment beats current experiment.
        """
        score = (sum((len(strip.faces) for strip in experiment.strips), 0.0)
                 / len(experiment.strips))
        if score > self.best_score:
            self.best_score = score
            self.best_experiment = experiment

    def clear(self):
        """Remove best experiment, to start a fresh sequence of
        experiments.
        """
        self.best_score = -1.0
        self.best_experiment = None

class TriangleStripifier(object):
    """Implementation of a triangle stripifier.

    Heavily adapted from NvTriStrip.
    Original can be found at http://developer.nvidia.com/view.asp?IO=nvtristrip_library.
    """

    def __init__(self, mesh):
        self.num_samples = 10
        self.mesh = mesh

    @staticmethod
    def sample(population, k):
        """Return a k length list of unique elements chosen from the
        population sequence. Used for random sampling without
        replacement. Deterministic version of random.sample (being
        deterministic means that it is easier to test).

        >>> TriangleStripifier.sample(range(10), 1)
        [0]
        >>> TriangleStripifier.sample(range(10), 2)
        [0, 9]
        >>> TriangleStripifier.sample(range(10), 3)
        [0, 4, 9]
        >>> TriangleStripifier.sample(range(10), 4)
        [0, 3, 6, 9]
        >>> TriangleStripifier.sample(range(10), 5)
        [0, 2, 4, 6, 9]
        >>> TriangleStripifier.sample(range(10), 6)
        [0, 1, 3, 5, 7, 9]
        >>> TriangleStripifier.sample(range(10), 7)
        [0, 1, 3, 4, 6, 7, 9]
        >>> TriangleStripifier.sample(range(10), 8)
        [0, 1, 2, 3, 5, 6, 7, 9]
        >>> TriangleStripifier.sample(range(10), 9)
        [0, 1, 2, 3, 4, 5, 6, 7, 9]
        >>> TriangleStripifier.sample(range(10), 10)
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        """
        if k == 1:
            # corner case
            return [population[0]]
        else:
            # all other cases
            return [
                population[int((i * (float(len(population)) - 1)) / (k - 1))]
                for i in xrange(k)]

    def find_all_strips(self):
        """Find all strips.

        Empty mesh
        ----------

        >>> m = Mesh()
        >>> m.lock()
        >>> ts = TriangleStripifier(m)
        >>> ts.find_all_strips()
        []

        Full mesh
        ---------

        >>> m = Mesh()
        >>> tmp = m.add_face(2, 1, 7)
        >>> tmp = m.add_face(0, 1, 2)
        >>> tmp = m.add_face(2, 7, 4) # in strip
        >>> tmp = m.add_face(4, 7, 11) # in strip
        >>> tmp = m.add_face(5, 3, 2)
        >>> tmp = m.add_face(1, 0, 8) # in strip
        >>> tmp = m.add_face(0, 8, 9) # bad orientation!
        >>> tmp = m.add_face(8, 0, 10) # in strip
        >>> tmp = m.add_face(10, 11, 8) # in strip
        >>> # parallel strip
        >>> tmp = m.add_face(0, 2, 21) # in strip
        >>> tmp = m.add_face(21, 2, 22) # in strip
        >>> tmp = m.add_face(2, 4, 22) # in strip
        >>> tmp = m.add_face(21, 24, 0) # in strip
        >>> tmp = m.add_face(9, 0, 24) # in strip
        >>> # parallel strip, further down
        >>> tmp = m.add_face(8, 11, 31) # in strip
        >>> tmp = m.add_face(8, 31, 32) # in strip
        >>> tmp = m.add_face(31, 11, 33) # in strip
        >>> m.lock()
        >>> ts = TriangleStripifier(m)
        >>> sorted(ts.find_all_strips())
        [[3, 2, 5], [4, 22, 2, 21, 0, 24, 9], [9, 0, 8], [11, 4, 7, 2, 1, 0, 8, 10, 11], [32, 8, 31, 11, 33]]
        """
        all_strips = []
        selector = ExperimentSelector()
        unstripped_faces = set(xrange(len(self.mesh.faces)))
        while True:
            experiments = []
            # note: using deterministic self.sample
            # instead of existing random.sample in python
            # because deterministic version is easier to test
            for sample in self.sample(list(unstripped_faces),
                                      min(self.num_samples,
                                          len(unstripped_faces))):
                exp_face = self.mesh.faces[sample]
                for exp_vertex in exp_face.verts:
                    experiments.append(
                        Experiment(start_vertex=exp_vertex,
                                   start_face=exp_face))
            if not experiments:
                # done!
                return all_strips
            # note: use while loop so we only need to keep at most two
            # built experiments at the same time in memory
            while experiments:
                experiment = experiments.pop()
                experiment.build()
                selector.update(experiment)
            unstripped_faces -= selector.best_experiment.stripped_faces
            # remove stripped faces from mesh
            for strip in selector.best_experiment.strips:
                for face in strip.faces:
                    self.mesh.discard_face(face)
            # calculate actual strips for experiment
            all_strips.extend(
                (strip.get_strip()
                 for strip in selector.best_experiment.strips))
            selector.clear()

if __name__=='__main__':
    import doctest
    doctest.testmod()
