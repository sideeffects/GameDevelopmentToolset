"""A lightweight library for common vector and matrix operations."""

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

from itertools import izip
import logging
import operator

def float_to_int(value):
    """Convert float to integer, rounding and handling nan and inf
    gracefully.

    >>> float_to_int(0.4)
    0
    >>> float_to_int(-0.4)
    0
    >>> float_to_int(0.6)
    1
    >>> float_to_int(-0.6)
    -1
    >>> float_to_int(float('inf'))
    pyffi.utils.mathutils:WARNING:float_to_int converted +inf to +2147483648.
    2147483648
    >>> float_to_int(-float('inf'))
    pyffi.utils.mathutils:WARNING:float_to_int converted -inf to -2147483648.
    -2147483648
    >>> float_to_int(float('nan'))
    pyffi.utils.mathutils:WARNING:float_to_int converted nan to 0.
    0
    """
    try:
        return int(value + 0.5 if value > 0 else value - 0.5)
    except ValueError:
        logging.getLogger("pyffi.utils.mathutils").warn(
            "float_to_int converted nan to 0.")
        return 0
    except OverflowError:
        if value > 0:
            logging.getLogger("pyffi.utils.mathutils").warn(
                "float_to_int converted +inf to +2147483648.")
            return 2147483648
        else:
            logging.getLogger("pyffi.utils.mathutils").warn(
                "float_to_int converted -inf to -2147483648.")
            return -2147483648

def getBoundingBox(veclist):
    """Calculate bounding box (pair of vectors with minimum and maximum
    coordinates).

    >>> getBoundingBox([(0,0,0), (1,1,2), (0.5,0.5,0.5)])
    ((0, 0, 0), (1, 1, 2))"""
    if not veclist:
        # assume 3 dimensions if veclist is empty
        return (0,0,0), (0,0,0)

    # find bounding box
    dim = len(veclist[0])
    return (
        tuple((min(vec[i] for vec in veclist) for i in xrange(dim))),
        tuple((max(vec[i] for vec in veclist) for i in xrange(dim))))

def getCenterRadius(veclist):
    """Calculate center and radius of given list of vectors.

    >>> getCenterRadius([(0,0,0), (1,1,2), (0.5,0.5,0.5)]) # doctest: +ELLIPSIS
    ((0.5, 0.5, 1.0), 1.2247...)
    """
    if not veclist:
        # assume 3 dimensions if veclist is empty
        return (0,0,0), 0

    # get bounding box
    vecmin, vecmax = getBoundingBox(veclist)

    # center is in the center of the bounding box
    center = tuple((minco + maxco) * 0.5
                   for minco, maxco in izip(vecmin, vecmax))

    # radius is the largest distance from the center
    r2 = 0.0
    for vec in veclist:
        dist = vecSub(center, vec)
        r2 = max(r2, vecDotProduct(dist, dist))
    radius = r2 ** 0.5

    return center, radius

def vecSub(vec1, vec2):
    """Vector substraction."""
    return tuple(x - y for x, y in izip(vec1, vec2))

def vecAdd(vec1, vec2):
    return tuple(x + y for x, y in izip(vec1, vec2))

def vecscalarMul(vec, scalar):
    return tuple(x * scalar for x in vec)

def vecDotProduct(vec1, vec2):
    """The vector dot product (any dimension).

    >>> vecDotProduct((1,2,3),(4,-5,6))
    12"""
    return sum(x1 * x2 for x1, x2 in izip(vec1, vec2))

def vecDistance(vec1, vec2):
    """Return distance between two vectors (any dimension).

    >>> vecDistance((1,2,3),(4,-5,6)) # doctest: +ELLIPSIS
    8.185...
    """
    return vecNorm(vecSub(vec1, vec2))

def vecNormal(vec1, vec2, vec3):
    """Returns a vector that is orthogonal on C{triangle}."""
    return vecCrossProduct(vecSub(vec2, vec1), vecSub(vec3, vec1))

def vecDistanceAxis(axis, vec):
    """Return distance between the axis spanned by axis[0] and axis[1] and the
    vector v, in 3 dimensions. Raises ZeroDivisionError if the axis points
    coincide.

    >>> vecDistanceAxis([(0,0,0), (0,0,1)], (0,3.5,0))
    3.5
    >>> vecDistanceAxis([(0,0,0), (1,1,1)], (0,1,0.5)) # doctest: +ELLIPSIS
    0.70710678...
    """
    return vecNorm(vecNormal(axis[0], axis[1], vec)) / vecDistance(*axis)

def vecDistanceTriangle(triangle, vert):
    """Return (signed) distance between the plane spanned by triangle[0],
    triangle[1], and triange[2], and the vector v, in 3 dimensions.

    >>> vecDistanceTriangle([(0,0,0),(1,0,0),(0,1,0)], (0,0,1))
    1.0
    >>> vecDistanceTriangle([(0,0,0),(0,1,0),(1,0,0)], (0,0,1))
    -1.0
    """
    normal = vecNormal(*triangle)
    return vecDotProduct(normal, vecSub(vert, triangle[0])) \
           / vecNorm(normal)

def vecNorm(vec):
    """Norm of a vector (any dimension).

    >>> vecNorm((2,3,4)) # doctest: +ELLIPSIS
    5.3851648...
    """
    return vecDotProduct(vec, vec) ** 0.5

def vecNormalized(vec):
    """Normalized version of a vector (any dimension).

    >>> vecNormalized((2,3,4)) # doctest: +ELLIPSIS
    (0.371..., 0.557..., 0.742...)
    """
    return vecscalarMul(vec, 1.0 / vecNorm(vec))

def vecCrossProduct(vec1, vec2):
    """The vector cross product (in 3d).

    >>> vecCrossProduct((1,0,0),(0,1,0))
    (0, 0, 1)
    >>> vecCrossProduct((1,2,3),(4,5,6))
    (-3, 6, -3)
    """
    return (vec1[1] * vec2[2] - vec1[2] * vec2[1],
            vec1[2] * vec2[0] - vec1[0] * vec2[2],
            vec1[0] * vec2[1] - vec1[1] * vec2[0])

def matTransposed(mat):
    """Return the transposed of a nxn matrix.

    >>> matTransposed(((1, 2), (3, 4)))
    ((1, 3), (2, 4))"""
    dim = len(mat)
    return tuple( tuple( mat[i][j]
                         for i in xrange(dim) )
                  for j in xrange(dim) )

def matscalarMul(mat, scalar):
    """Return matrix * scalar."""
    dim = len(mat)
    return tuple( tuple( mat[i][j] * scalar
                         for j in xrange(dim) )
                  for i in xrange(dim) )

def matvecMul(mat, vec):
    """Return matrix * vector."""
    dim = len(mat)
    return tuple( sum( mat[i][j] * vec[j] for j in xrange(dim) )
                  for i in xrange(dim) )

def matMul(mat1, mat2):
    """Return matrix * matrix."""
    dim = len(mat1)
    return tuple( tuple( sum( mat1[i][k] * mat2[k][j]
                              for k in xrange(dim) )
                         for j in xrange(dim) )
                  for i in xrange(dim) )

def matAdd(mat1, mat2):
    """Return matrix + matrix."""
    dim = len(mat1)
    return tuple( tuple( mat1[i][j] + mat2[i][j]
                         for j in xrange(dim) )
                  for i in xrange(dim) )

def matSub(mat1, mat2):
    """Return matrix - matrix."""
    dim = len(mat1)
    return tuple( tuple( mat1[i][j] - mat2[i][j]
                         for j in xrange(dim) )
                  for i in xrange(dim) )

def matCofactor(mat, i, j):
    dim = len(mat)
    return matDeterminant(tuple( tuple( mat[ii][jj]
                                        for jj in xrange(dim)
                                        if jj != j )
                                 for ii in xrange(dim)
                                 if ii != i ))

def matDeterminant(mat):
    """Calculate determinant.

    >>> matDeterminant( ((1,2,3), (4,5,6), (7,8,9)) )
    0
    >>> matDeterminant( ((1,2,4), (3,0,2), (-3,6,2)) )
    36
    """
    dim = len(mat)
    if dim == 0: return 0
    elif dim == 1: return mat[0][0]
    elif dim == 2: return mat[0][0] * mat[1][1] - mat[1][0] * mat[0][1]
    else:
        return sum( (-1 if i&1 else 1) * mat[i][0] * matCofactor(mat, i, 0)
                    for i in xrange(dim) )

if __name__ == "__main__":
    import doctest
    doctest.testmod()
