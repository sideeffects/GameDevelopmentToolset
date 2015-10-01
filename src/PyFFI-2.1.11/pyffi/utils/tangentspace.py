"""A module for tangent space calculation."""

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

from pyffi.utils.mathutils import *

def getTangentSpace(vertices = None, normals = None, uvs = None,
                    triangles = None, orientation = False,
                    orthogonal = True):
    """Calculate tangent space data.

    >>> vertices = [(0,0,0), (0,1,0), (1,0,0)]
    >>> normals = [(0,0,1), (0,0,1), (0,0,1)]
    >>> uvs = [(0,0), (0,1), (1,0)]
    >>> triangles = [(0,1,2)]
    >>> getTangentSpace(vertices = vertices, normals = normals, uvs = uvs, triangles = triangles)
    ([(0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0)], [(1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)])

    :param vertices: A list of vertices (triples of floats/ints).
    :param normals: A list of normals (triples of floats/ints).
    :param uvs: A list of uvs (pairs of floats/ints).
    :param triangles: A list of triangle indices (triples of ints).
    :param orientation: Set to ``True`` to return orientation (this is used by
        for instance Crysis).
    :return: Two lists of vectors, tangents and binormals. If C{orientation}
        is ``True``, then returns an extra list with orientations (containing
        floats which describe the total signed surface of all faces sharing
        the particular vertex).
    """

    # validate input
    if len(vertices) != len(normals) or len(vertices) != len(uvs):
        raise ValueError(
            "lists of vertices, normals, and uvs must have the same length")

    bin = [(0,0,0) for i in xrange(len(vertices)) ]
    tan = [(0,0,0) for i in xrange(len(vertices)) ]
    orientations = [0 for i in xrange(len(vertices))]

    # calculate tangents and binormals from vertex and texture coordinates
    for t1, t2, t3 in triangles:
        # skip degenerate triangles
        if t1 == t2 or t2 == t3 or t3 == t1:
            continue

        # get vertices, uvs, and directions of the triangle
        v1 = vertices[t1]
        v2 = vertices[t2]
        v3 = vertices[t3]
        w1 = uvs[t1]
        w2 = uvs[t2]
        w3 = uvs[t3]
        v2v1 = vecSub(v2, v1)
        v3v1 = vecSub(v3, v1)
        w2w1 = vecSub(w2, w1)
        w3w1 = vecSub(w3, w1)

        # surface of triangle in texture space
        r = w2w1[0] * w3w1[1] - w3w1[0] * w2w1[1]

        # sign of surface
        r_sign = (1 if r >= 0 else -1)

        # contribution of this triangle to tangents and binormals
        sdir = (
            r_sign * (w3w1[1] * v2v1[0] - w2w1[1] * v3v1[0]),
            r_sign * (w3w1[1] * v2v1[1] - w2w1[1] * v3v1[1]),
            r_sign * (w3w1[1] * v2v1[2] - w2w1[1] * v3v1[2]))
        try:
            sdir = vecNormalized(sdir)
        except ZeroDivisionError: # catches zero vector
            continue # skip triangle
        except ValueError: # catches invalid data
            continue # skip triangle

        tdir = (
            r_sign * (w2w1[0] * v3v1[0] - w3w1[0] * v2v1[0]),
            r_sign * (w2w1[0] * v3v1[1] - w3w1[0] * v2v1[1]),
            r_sign * (w2w1[0] * v3v1[2] - w3w1[0] * v2v1[2]))
        try:
            tdir = vecNormalized(tdir)
        except ZeroDivisionError: # catches zero vector
            continue # skip triangle
        except ValueError: # catches invalid data
            continue # skip triangle

        # vector combination algorithm could possibly be improved
        for i in (t1, t2, t3):
            tan[i] = vecAdd(tan[i], tdir)
            bin[i] = vecAdd(bin[i], sdir)
            orientations[i] += r

    # convert into orthogonal space
    xvec = (1, 0, 0)
    yvec = (0, 1, 0)
    for i, norm in enumerate(normals):
        if abs(1-vecNorm(norm)) > 0.01:
            raise ValueError(
                "tangentspace: unnormalized normal in list of normals (%s, norm is %f)" % (norm, vecNorm(norm)))
        try:
            # turn norm, bin, tan into a base via Gram-Schmidt
            bin[i] = vecSub(bin[i],
                            vecscalarMul(
                                norm,
                                vecDotProduct(norm, bin[i])))
            bin[i] = vecNormalized(bin[i])
            tan[i] = vecSub(tan[i],
                            vecscalarMul(
                                norm,
                                vecDotProduct(norm, tan[i])))
            tan[i] = vecSub(tan[i],
                            vecscalarMul(
                                bin[i],
                                vecDotProduct(norm, bin[i])))
            tan[i] = vecNormalized(tan[i])
        except ZeroDivisionError:
            # insuffient data to set tangent space for this vertex
            # in that case pick a space
            bin[i] = vecCrossProduct(xvec, norm)
            try:
                bin[i] = vecNormalized(bin[i])
            except ZeroDivisionError:
                bin[i] = vecCrossProduct(yvec, norm)
                bin[i] = vecNormalized(bin[i])
            tan[i] = vecCrossProduct(norm, bin[i])

    # return result
    if orientation:
        return tan, bin, orientations
    else:
        return tan, bin

if __name__ == "__main__":
    import doctest
    doctest.testmod()
