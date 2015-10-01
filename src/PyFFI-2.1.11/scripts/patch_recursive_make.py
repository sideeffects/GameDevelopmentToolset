#!/usr/bin/python

"""A tool to make binary patches between folders recursively."""

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

import argparse
import shutil
import os
import os.path
import subprocess

# configuration options

parser = argparse.ArgumentParser(
    description=__doc__,
    epilog=
    "All additional arguments are passed to the patch command CMD.")
parser.add_argument(
    'patch_cmd', metavar="CMD", type=str,
    help="use CMD to make a patch between files; this command must "
    "accept at least 3 arguments: 'CMD oldfile newfile patchfile ...'")
parser.add_argument(
    'in_folder', type=str,
    help="folder containing original files")
parser.add_argument(
    'out_folder', type=str,
    help="folder containing updated files")
parser.add_argument(
    'patch_folder', type=str,
    help="folder where patch files will be stored (should be empty)")
args, unknown_args = parser.parse_known_args()

# actual script

def patch_cmd(in_file, out_file, patch_file):
    # in_file must exist by construction of the script
    if not os.path.exists(in_file):
        raise RuntimeError("in file %s not found; bug?")
    # create folder for patch_file, if it does not yet exist
    folder = os.path.split(patch_file)[0]
    if not os.path.exists(folder):
        os.makedirs(folder)
    # make patch if out_file exists
    if os.path.exists(out_file):
        command = [args.patch_cmd, in_file, out_file, patch_file] + unknown_args
        print("making %s" % patch_file)
        subprocess.call(command)
    else:
        print("skipped %s (no out file)" % in_file)
        return

for dirpath, dirnames, filenames in os.walk(args.in_folder):
    for filename in filenames:
        in_file = os.path.join(dirpath, filename)
        out_file = in_file.replace(args.in_folder, args.out_folder, 1)
        patch_file = in_file.replace(args.in_folder, args.patch_folder, 1)
        patch_file += ".patch"
        patch_cmd(in_file, out_file, patch_file)
