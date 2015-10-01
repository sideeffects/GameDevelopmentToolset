#!/usr/bin/python

"""An unpack tool for rockstar .dir/.img files.

For example, consider the following folder layout, within the current folder::

  archive/Test.dir
  archive/Test.img
  archive/World.dir
  archive/World.img
  unpacked/

Within the current folder, call::

  C:\Python26\python.exe C:\Python26\Scripts\rockstar_pack_dir_img.py archive unpacked

The unpacked files will then reside in

  unpacked/Test/*.*
  unpacked/World/*.*

Beware that the .img format can only store files whose size is a
multiple of 2048. Files of a different size are padded with zeros.
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

import os
import os.path
from optparse import OptionParser

from pyffi.formats.rockstar.dir_ import DirFormat

# configuration options

parser = OptionParser(
    usage=
    "Usage: %prog source_folder destination_folder\n\n"
    + __doc__
    )
(options, args) = parser.parse_args()
if len(args) != 2:
    parser.print_help()
    exit()
in_folder, unpack_folder = args

# actual script

def unpack(arcroot):
    dirdata = DirFormat.Data()
    with open(os.path.join(in_folder, arcroot) + '.dir', 'rb') as dirfile:
        dirdata.read(dirfile)
    folder = os.path.join(unpack_folder, arcroot)
    print("unpacking to %s" % folder)
    os.mkdir(folder)
    with open(os.path.join(in_folder, arcroot) + '.img', 'rb') as imgfile:
        dirdata.unpack(imgfile, folder)

for arcname in os.listdir(in_folder):
    if (arcname.endswith('.dir')
        and os.path.isfile(os.path.join(in_folder, arcname))):
        unpack(arcname[:-4])
