"""Create mopps using mopper.exe"""

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

import os.path
import tempfile
import subprocess
import sys

def _skip_terminal_chars(stream):
    """Skip initial terminal characters (happens when mopper runs via wine)."""
    firstline = stream.readline()
    if '\x1b' in firstline:
        stream.seek(firstline.rfind('\x1b') + 2)
    else:
        stream.seek(0)

def getMopperPath():
    """Get path to the mopper.

    >>> path = getMopperPath()
    >>> path.endswith("mopper.exe")
    True

    :raise ``OSError``: If mopper.exe is not found.
    :return: Path to mopper.exe.
    :rtype: ``str``
    """
    mopper = os.path.join(os.path.dirname(__file__), "mopper.exe")
    if not os.path.exists(mopper):
        raise OSError("mopper.exe not found at %s" % mopper)
    return mopper

def getMopperCredits():
    """Get info about mopper, and credit havok.

    >>> print(getMopperCredits())
    Mopper. Copyright (c) 2008, NIF File Format Library and Tools.
    All rights reserved.
    <BLANKLINE>
    Options:
      --help      for usage help
      --license   for licensing details
    <BLANKLINE>
    Mopper uses havok. Copyright 1999-2008 Havok.com Inc. (and its Licensors).
    All Rights Reserved. See www.havok.com for details.
    <BLANKLINE>
    <BLANKLINE>

    :raise ``OSError``: If mopper.exe is not found or cannot run.
    :return: Credits string.
    :rtype: ``str``
    """
    mopper = getMopperPath()
    outfile = tempfile.TemporaryFile("w+") # not binary
    try:
        # get license info, credit havok (raises OSError on failure)
        if sys.platform == "win32":
            subprocess.call([mopper], stdout=outfile)
        else:
            subprocess.call(["wine", mopper], stdout=outfile)
        outfile.seek(0)
        _skip_terminal_chars(outfile)
        creditstr = outfile.read().replace("\r\n", "\n")
    finally:
        outfile.close()
    return creditstr

def getMopperOriginScaleCodeWelding(vertices, triangles, material_indices=None):
    """Generate mopp code and welding info for given geometry. Raises
    RuntimeError if something goes wrong (e.g. if mopp generator fails, or if
    mopper.exe cannot be run on the current platform).

    Call L{getMopperCredits} before calling this function if you need to credit
    havok in a console application that uses this function.

    For example, creating a mopp for the standard cube:

    >>> expected_moppcode = [
    ...     40, 0, 255, 39, 0, 255, 38, 0, 255, 19, 129, 125, 41, 22, 130,
    ...     125, 12, 24, 130, 125, 4, 38, 0, 5, 51, 39, 0, 5, 50, 24, 130,
    ...     125, 4, 40, 0, 5, 59, 16, 255, 249, 12, 20, 130, 125, 4, 39,
    ...     0, 5, 53, 40, 0, 5, 49, 54, 22, 130, 125, 25, 24, 130, 125, 17,
    ...     17, 255, 249, 12, 21, 129, 125, 4, 38, 0, 5, 57, 40, 249, 255,
    ...     58, 56, 40, 249, 255, 52, 24, 130, 125, 4, 39, 249, 255, 55, 38,
    ...     249, 255, 48]
    >>> orig, scale, moppcode, welding_info = getMopperOriginScaleCodeWelding(
    ...     [(1, 1, 1), (0, 0, 0), (0, 0, 1), (0, 1, 0),
    ...      (1, 0, 1), (0, 1, 1), (1, 1, 0), (1, 0, 0)],
    ...     [(0, 4, 6), (1, 6, 7), (2, 1, 4), (3, 1, 2),
    ...      (0, 2, 4), (4, 1, 7), (6, 4, 7), (3, 0, 6),
    ...      (0, 3, 5), (3, 2, 5), (2, 0, 5), (1, 3, 6)])
    >>> scale
    16319749.0
    >>> ["%6.3f" % value for value in orig]
    ['-0.010', '-0.010', '-0.010']
    >>> moppcode == expected_moppcode
    True
    >>> welding_info
    [23030, 23247, 23030, 16086, 23247, 23247, 23247, 23247, 23247, 23247, 23247, 16086]

    :raise ``RuntimeError``: If the mopper has bad output.
    :raise ``OSError``: If the mopper is not found or cannot run.
    :param vertices: List of vertices.
    :type vertices: list of tuples of floats
    :param triangles: List of triangles (indices referring back to vertex list).
    :type triangles: list of tuples of ints
    :param material_indices: List of material indices (optional).
    :type material_indices: list of ints
    :return: The origin as a tuple of floats, the mopp scale as a float,
        the mopp code as a list of ints, and the welding info as a list of
        ints.
    :rtype: ``tuple`` of ``float``\ s, ``float``, ``list`` of ``int``\ s, and ``list``
        of ``int``\ s
    """

    if material_indices is None:
        material_indices = []

    mopper = getMopperPath()
    infile = tempfile.TemporaryFile("w+") # not binary
    outfile = tempfile.TemporaryFile("w+") # not binary
    try:
        # set up input
        infile.write("%i\n" % len(vertices))
        for vert in vertices:
            infile.write("%f %f %f\n" % vert)
        infile.write("\n%i\n" % len(triangles))
        for tri in triangles:
            infile.write("%i %i %i\n" % tri)
        infile.write("\n%i\n" % len(material_indices))
        for matindex in material_indices:
            infile.write("%i\n" % matindex)
        infile.seek(0)
        # call mopper (raises OSError on failure)
        if sys.platform == "win32":
            subprocess.call([mopper, "--"], stdin=infile, stdout=outfile)
        else:
            subprocess.call(["wine", mopper, "--"], stdin=infile, stdout=outfile)
        # process output
        outfile.seek(0)
        _skip_terminal_chars(outfile)
        try:
            origin = tuple(float(outfile.readline()) for i in xrange(3))
            scale = float(outfile.readline())
            moppcodelen = int(outfile.readline())
            moppcode = [int(outfile.readline()) for i in xrange(moppcodelen)]
            welding_info_len = int(outfile.readline())
            welding_info = [int(outfile.readline())
                            for i in xrange(welding_info_len)]
        except ValueError:
            # conversion failed
            raise RuntimeError("invalid mopper output (mopper failed?)")
    finally:
        infile.close()
        outfile.close()
    return origin, scale, moppcode, welding_info

if __name__ == "__main__":
    import doctest
    doctest.testmod()

