#!/usr/bin/python

"""Make hex structure libraries for all nif versions.

Installation
------------

Make sure you have PyFFI installed (see http://pyffi.sourceforge.net).

Then, copy makehsl.py to your Hex Workshop structures folder

  C:\Program Files\BreakPoint Software\Hex Workshop 4.2\Structures

and run it. This will create a .hsl file per nif version.

Known issues
------------

Hex Workshop libraries cannot properly deal with conditionals, so
for serious hacking you probably want to edit the .hsl library as you
go, commenting out the parts which are not present in the particular
block you are investigating.
"""

# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007-2011, NIF File Format Library and Tools.
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
#    * Neither the name of the NIF File Format Library and Tools
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
# --------------------------------------------------------------------------

import sys
from types import *
from string import maketrans

from pyffi.formats.nif import NifFormat
from pyffi.object_models.xml.basic import BasicBase

def find_templates():
    # find all types that are used as a template (excluding the ones
    # occuring in Ref & its subclass Ptr)
    templates = set()
    for cls in NifFormat.xml_struct:
        for attr in cls._attribute_list:
            if attr.template != None and attr.template != type(None) and not issubclass(attr.type_, NifFormat.Ref):
                templates.add(attr.template)
    return templates

transtable = maketrans('?', '_')
def sanitize_attrname(s):
    return s.translate(transtable)

def write_hsl(f, ver, templates):
    # map basic NifFormat types to HWS types and enum byte size
    hsl_types = {
        NifFormat.int    : ('long', 4),
        NifFormat.uint   : ('ulong', 4),
        NifFormat.short  : ('short', 2),
        NifFormat.ushort : ('ushort', 2),
        NifFormat.Flags  : ('ushort', None),
        NifFormat.byte   : ('ubyte ', 1),
        NifFormat.char   : ('char', None),
        NifFormat.float  : ('float', None),
        NifFormat.Ref    : ('long', None),
        NifFormat.Ptr    : ('long', None),
        NifFormat.FileVersion : ('ulong', None),
        # some stuff we cannot do in hex workshop
        NifFormat.HeaderString : ('char', None),
        NifFormat.LineString : ('char', None) }
        # hack for string (TODO fix this in NifFormat)
        #NifFormat.string : ('struct string', None) }

    if ver <= 0x04000002:
        hsl_types[NifFormat.bool] = ('ulong', 4)
    else:
        hsl_types[NifFormat.bool] = ('ubyte ', 1)

    # write header
    f.write("""// hex structure library for NIF Format 0x%08X
#include "standard-types.hsl"
#pragma byteorder(little_endian)
#pragma maxarray(65535)

"""%ver)

    # write each enum class
    for cls in NifFormat.xml_enum:
        write_enum(cls, ver, hsl_types, f)

    # write each struct class
    for cls in NifFormat.xml_struct:
        if cls.__name__[:3] == 'ns ': continue # cheat: skip ns types
        if not cls._is_template:
            # write regular class
            write_struct(cls, ver, hsl_types, f, None)
        else:
            # write template classes
            for template in templates:
                write_struct(cls, ver, hsl_types, f, template)

def write_enum(cls, ver, hsl_types, f):
    # set enum size
    f.write('#pragma enumsize(%s)\n' % cls._numbytes)
    f.write('typedef enum tag' + cls.__name__ + ' {\n')
    ## list of all non-private attributes gives enum constants
    #enum_items = [x for x in cls.__dict__.items() if x[0][:2] != '__']
    ## sort them by value
    #enum_items = sorted(enum_items, key=lambda x: x[1])
    # and write out all name, value pairs
    enum_items = zip(cls._enumkeys, cls._enumvalues)
    for const_name, const_value in enum_items[:-1]:
        f.write('  ' + const_name + ' = ' + str(const_value) + ',\n')
    const_name, const_value = enum_items[-1]
    f.write('  ' + const_name + ' = ' + str(const_value) + '\n')
    f.write('} ' + cls.__name__ + ';\n\n')

def write_struct(cls, ver, hsl_types, f, template):
    # open the structure
    if not template:
        f.write('struct ' + cls.__name__ + ' {\n')
    else:
        f.write('struct ' + cls.__name__ + '_' + template.__name__ + ' {\n')
    #for attrname, typ, default, tmpl, arg, arr1, arr2, cond, ver1, ver2, userver, doc in cls._attribute_list:
    for attr in cls._attribute_list:
        # check version
        if not (ver is None):
            if (not (attr.ver1 is None)) and ver < attr.ver1:
                continue
            if (not (attr.ver2 is None)) and ver > attr.ver2:
                continue

        s = '  '

        # things that can only be determined at runtime (rt_xxx)
        rt_type = attr.type_ if attr.type_ != type(None) \
                  else template
        rt_template = attr.template if attr.template != type(None) \
                      else template

        # get the attribute type name
        try:
            s += hsl_types[rt_type][0]
        except KeyError:
            if rt_type in NifFormat.xml_enum:
                s += rt_type.__name__
            else: # it's in NifFormat.xml_struct
                s += 'struct ' + rt_type.__name__
        # get the attribute template type name
        if (not rt_template is None) and (not issubclass(rt_type, NifFormat.Ref)):
            s += '_'
            s += rt_template.__name__ # note: basic types are named by their xml name in the template
        # attribute name
        s = s.ljust(20) + ' ' + sanitize_attrname(attr.name)
        # array and conditional arguments
        arr_str = ''
        comments = ''
        if not attr.cond is None:
            # catch argument passing and double arrays
            if (str(attr.cond).find('arg') == -1) and (attr.arr2 is None):
                if attr.cond._op is None or (attr.cond._op == '!=' and attr.cond._right == 0):
                    arr_str += sanitize_attrname(str(attr.cond._left))
                else:
                    comments += ' (' + sanitize_attrname(str(attr.cond)) + ')'
            else:
                comments += ' (' + sanitize_attrname(str(attr.cond)) + ')'
        if attr.arr1 is None:
            pass
        elif attr.arr2 is None:
            if str(attr.arr1).find('arg') == -1: # catch argument passing
                if arr_str:
                    arr_str += ' * '
                arr_str += sanitize_attrname(str(attr.arr1._left))
                if attr.arr1._op:
                    comments += ' [' + sanitize_attrname(str(attr.arr1)) + ']'
            else:
                if arr_str:
                    arr_str += ' * '
                arr_str += '1'
                comments += ' [arg]'
        else:
            # TODO catch args here too (so far not used anywhere in nif.xml)
            if arr_str:
                arr_str += ' * '
            arr_str += sanitize_attrname(str(attr.arr1._left)) + ' * ' + sanitize_attrname(str(attr.arr2._left))
            if attr.arr1._op or attr.arr2._op:
                comments += ' [' + sanitize_attrname(str(attr.arr1)) + ' * ' + sanitize_attrname(str(attr.arr2)) + ']'
        arr_str = '[' + arr_str + ']' if arr_str else ''
        comments = ' //' + comments if comments else ''
        f.write(s + arr_str + ';' + comments + '\n')
    # close the structure
    f.write('};\n\n')

if __name__ == '__main__':
    # list all types used as a template
    templates = find_templates()
    # write out hex structure library for each nif version
    for ver_str, ver in NifFormat.versions.items():
        f = open('nif_' + ver_str.replace('.', '_') + '.hsl', 'w')
        try:
            write_hsl(f, ver, templates)
        finally:
            f.close()
