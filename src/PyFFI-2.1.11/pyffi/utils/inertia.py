"""Calculate the mass, center of gravity, and inertia matrix for common
shapes."""

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

import math
from pyffi.utils.mathutils import *

# see http://en.wikipedia.org/wiki/List_of_moment_of_inertia_tensors

def getMassInertiaSphere(radius, density = 1, solid = True):
    """Return mass and inertia matrix for a sphere of given radius and
    density.

    >>> mass, inertia_matrix = getMassInertiaSphere(2.0, 3.0)
    >>> mass # doctest: +ELLIPSIS
    100.53096...
    >>> inertia_matrix[0][0] # doctest: +ELLIPSIS
    160.84954..."""
    if solid:
        mass = density * (4 * math.pi * (radius ** 3)) / 3
        inertia = (2 * mass * (radius ** 2)) / 5
    else:
        mass = density * 4 * math.pi * (radius ** 2)
        inertia = (2 * mass * (radius ** 2)) / 3

    return mass, tuple( tuple( (inertia if i == j else 0)
                               for i in xrange(3) )
                        for j in xrange(3) )

def getMassInertiaBox(size, density = 1, solid = True):
    """Return mass and inertia matrix for a box of given size and
    density.

    >>> mass, inertia = getMassInertiaBox((1.0, 2.0, 3.0), 4.0)
    >>> mass
    24.0
    >>> inertia
    ((26.0, 0, 0), (0, 20.0, 0), (0, 0, 10.0))
    """
    assert(len(size) == 3) # debug
    if solid:
        mass = density * size[0] * size[1] * size[2]
        tmp = tuple(mass * (length ** 2) / 12.0 for length in size)
    else:
        mass = density * sum( x * x for x in size)
        tmp = tuple(mass * (length ** 2) / 6.0 for length in size) # just guessing here, todo calculate it
    return mass, ( ( tmp[1] + tmp[2], 0, 0 ),
                   ( 0, tmp[2] + tmp[0], 0 ),
                   ( 0, 0, tmp[0] + tmp[1] ) )

def getMassInertiaCapsule(length, radius, density = 1, solid = True):
    # cylinder + caps, and caps have volume of a sphere
    if solid:
        mass = density * (length * math.pi * (radius ** 2)
                          + (4 * math.pi * (radius ** 3)) / 3)

        # approximate by cylinder
        # TODO: also include the caps into the inertia matrix
        inertia_xx = mass * (3 * (radius ** 2) + (length ** 2)) / 12.0
        inertia_yy = inertia_xx
        inertia_zz = 0.5 * mass * (radius ** 2)
    else:
        mass = density * (length * 2 * math.pi * radius
                          + 2 * math.pi * (radius ** 2))
        inertia_xx = mass * (6 * (radius ** 2) + (length ** 2)) / 12.0
        inertia_yy = inertia_xx
        inertia_zz = mass * (radius ** 2)

    return mass,  ( ( inertia_xx, 0, 0 ),
                    ( 0, inertia_yy, 0 ),
                    ( 0, 0, inertia_zz ) )

#
# References
# ----------
#
# Jonathan Blow, Atman J Binstock
# "How to find the inertia tensor (or other mass properties) of a 3D solid body represented by a triangle mesh"
# http://number-none.com/blow/inertia/bb_inertia.doc
#
# David Eberly
# "Polyhedral Mass Properties (Revisited)"
# http://www.geometrictools.com//LibPhysics/RigidBody/Wm4PolyhedralMassProperties.pdf
#
# The function is an implementation of the Blow and Binstock algorithm,
# extended for the case where the polygon is a surface (set parameter
# solid = False).
def get_mass_center_inertia_polyhedron(vertices, triangles, density = 1, solid = True):
    """Return mass, center of gravity, and inertia matrix for a polyhedron.

    >>> from pyffi.utils.quickhull import qhull3d
    >>> box = [(0,0,0),(1,0,0),(0,2,0),(0,0,3),(1,2,0),(0,2,3),(1,0,3),(1,2,3)]
    >>> vertices, triangles = qhull3d(box)
    >>> mass, center, inertia = get_mass_center_inertia_polyhedron(
    ...     vertices, triangles, density = 4)
    >>> mass
    24.0
    >>> center
    (0.5, 1.0, 1.5)
    >>> inertia
    ((26.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 10.0))
    >>> poly = [(3,0,0),(0,3,0),(-3,0,0),(0,-3,0),(0,0,3),(0,0,-3)] # very rough approximation of a sphere of radius 2
    >>> vertices, triangles = qhull3d(poly)
    >>> mass, center, inertia = get_mass_center_inertia_polyhedron(
    ...     vertices, triangles, density = 3)
    >>> mass
    108.0
    >>> center
    (0.0, 0.0, 0.0)
    >>> abs(inertia[0][0] - 194.4) < 0.0001
    True
    >>> abs(inertia[1][1] - 194.4) < 0.0001
    True
    >>> abs(inertia[2][2] - 194.4) < 0.0001
    True
    >>> abs(inertia[0][1]) < 0.0001
    True
    >>> abs(inertia[0][2]) < 0.0001
    True
    >>> abs(inertia[1][2]) < 0.0001
    True
    >>> sphere = []
    >>> N = 10
    >>> for j in range(-N+1, N):
    ...     theta = j * 0.5 * math.pi / N
    ...     st, ct = math.sin(theta), math.cos(theta)
    ...     M = max(3, int(ct * 2 * N + 0.5))
    ...     for i in range(0, M):
    ...         phi = i * 2 * math.pi / M
    ...         s, c = math.sin(phi), math.cos(phi)
    ...         sphere.append((2*s*ct, 2*c*ct, 2*st)) # construct sphere of radius 2
    >>> sphere.append((0,0,2))
    >>> sphere.append((0,0,-2))
    >>> vertices, triangles = qhull3d(sphere)
    >>> mass, center, inertia = get_mass_center_inertia_polyhedron(
    ...     vertices, triangles, density = 3, solid = True)
    >>> abs(mass - 100.53) < 10 # 3*(4/3)*pi*2^3 = 100.53
    True
    >>> sum(abs(x) for x in center) < 0.01 # is center at origin?
    True
    >>> abs(inertia[0][0] - 160.84) < 10
    True
    >>> mass, center, inertia = get_mass_center_inertia_polyhedron(
    ...     vertices, triangles, density = 3, solid = False)
    >>> abs(mass - 150.79) < 10 # 3*4*pi*2^2 = 150.79
    True
    >>> abs(inertia[0][0] - mass*0.666*4) < 20 # m*(2/3)*2^2
    True
    """

    # 120 times the covariance matrix of the canonical tetrahedron
    # (0,0,0),(1,0,0),(0,1,0),(0,0,1)
    # integrate(integrate(integrate(z*z, x=0..1-y-z), y=0..1-z), z=0..1) = 1/120
    # integrate(integrate(integrate(y*z, x=0..1-y-z), y=0..1-z), z=0..1) = 1/60
    covariance_canonical = ( (2, 1, 1),
                             (1, 2, 1),
                             (1, 1, 2) )
    covariance_correction = 1.0/120

    covariances = []
    masses = []
    centers = []

    # for each triangle
    # construct a tetrahedron from triangle + (0,0,0)
    # find its matrix, mass, and center (for density = 1, will be corrected at
    # the end of the algorithm)
    for triangle in triangles:
        # get vertices
        vert0, vert1, vert2 = operator.itemgetter(*triangle)(vertices)

        # construct a transform matrix that converts the canonical tetrahedron
        # into (0,0,0),vert0,vert1,vert2
        transform_transposed = ( vert0, vert1, vert2 )
        transform = matTransposed(transform_transposed)

        # find the covariance matrix of the transformed tetrahedron/triangle
        if solid:
            # we shall be needing the determinant more than once, so
            # precalculate it
            determinant = matDeterminant(transform)
            # C' = det(A) * A * C * A^T
            covariances.append(
                matscalarMul(
                    matMul(matMul(transform,
                                  covariance_canonical),
                           transform_transposed),
                    determinant))
            # m = det(A) / 6.0
            masses.append(determinant / 6.0)
            # find center of gravity of the tetrahedron
            centers.append(tuple( 0.25 * sum(vert[i]
                                             for vert in (vert0, vert1, vert2))
                                  for i in xrange(3) ))
        else:
            # find center of gravity of the triangle
            centers.append(tuple( sum(vert[i]
                                      for vert in (vert0, vert1, vert2)) / 3.0
                                  for i in xrange(3) ))
            # find mass of triangle
            # mass is surface, which is half the norm of cross product
            # of two edges
            masses.append(
                vecNorm(vecCrossProduct(
                    vecSub(vert1, vert0), vecSub(vert2, vert0))) / 2.0)
            # find covariance at center of this triangle
            # (this is approximate only as it replaces triangle with point mass
            # todo: find better way)
            covariances.append(
                tuple(tuple( masses[-1]*x*y for x in centers[-1] )
                      for y in centers[-1]))

    # accumulate the results
    total_mass = sum(masses)
    if total_mass == 0:
        # dimension is probably badly chosen
        #raise ZeroDivisionError("mass is zero (consider calculating inertia with a lower dimension)")
        print("WARNING: mass is nearly zero (%f)" % total_mass)
        return 0, (0,0,0), ((0,0,0),(0,0,0),(0,0,0))
    # weighed average of centers with masses
    total_center = (0, 0, 0)
    for center, mass in izip(centers, masses):
        total_center = vecAdd(total_center,
                              vecscalarMul(center, mass / total_mass))
    # add covariances, and correct the values
    total_covariance = ((0,0,0),(0,0,0),(0,0,0))
    for covariance in covariances:
        total_covariance = matAdd(total_covariance, covariance)
    if solid:
        total_covariance = matscalarMul(total_covariance, covariance_correction)

    # translate covariance to center of gravity:
    # C' = C - m * ( x dx^T + dx x^T + dx dx^T )
    # with x the translation vector and dx the center of gravity
    translate_correction = matscalarMul(tuple(tuple(x * y
                                                    for x in total_center)
                                              for y in total_center),
                                        total_mass)
    total_covariance = matSub(total_covariance, translate_correction)

    # convert covariance matrix into inertia tensor
    trace = sum(total_covariance[i][i] for i in xrange(3))
    trace_matrix = tuple(tuple((trace if i == j else 0)
                               for i in xrange(3))
                         for j in xrange(3))
    total_inertia = matSub(trace_matrix, total_covariance)

    # correct for given density
    total_inertia = matscalarMul(total_inertia, density)
    total_mass *= density

    # correct negative mass
    if total_mass < 0:
        total_mass = -total_mass
        total_inertia = tuple(tuple(-x for x in row)
                              for row in total_inertia)

    return total_mass, total_center, total_inertia

if __name__ == "__main__":
    import doctest
    doctest.testmod()
