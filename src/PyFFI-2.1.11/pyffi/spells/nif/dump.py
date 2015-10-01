"""Spells for dumping particular blocks from nifs."""

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

import BaseHTTPServer
import ntpath # explicit windows style path manipulations
import os
import tempfile
import types
import webbrowser
from xml.sax.saxutils import escape # for htmlreport

from pyffi.formats.nif import NifFormat
from pyffi.spells.nif import NifSpell

def tohex(value, nbytes=4):
    """Improved version of hex."""
    return ("0x%%0%dX" % (2*nbytes)) % (long(str(value)) & (2**(nbytes*8)-1))

def dumpArray(arr):
    """Format an array.

    :param arr: An array.
    :type arr: L{pyffi.object_models.xml.array.Array}
    :return: String describing the array.
    """
    text = ""
    if arr._count2 == None:
        for i, element in enumerate(list.__iter__(arr)):
            if i > 16:
                text += "etc...\n"
                break
            text += "%i: %s\n" % (i, dumpAttr(element))
    else:
        k = 0
        for i, elemlist in enumerate(list.__iter__(arr)):
            for j, elem in enumerate(list.__iter__(elemlist)):
                if k > 16:
                    text += "etc...\n"
                    break
                text += "%i, %i: %s\n" % (i, j, dumpAttr(elem))
                k += 1
            if k > 16:
                break
    return text if text else "None"

def dumpBlock(block):
    """Return formatted string for block without following references.

    :param block: The block to print.
    :type block: L{NifFormat.NiObject}
    :return: String string describing the block.
    """
    text = '%s instance at 0x%08X\n' % (block.__class__.__name__, id(block))
    for attr in block._get_filtered_attribute_list():
        attr_str_lines = \
            dumpAttr(getattr(block, "_%s_value_" % attr.name)).splitlines()
        if len(attr_str_lines) > 1:
            text += '* %s :\n' % attr.name
            for attr_str in attr_str_lines:
                text += '    %s\n' % attr_str
        elif attr_str_lines:
            text += '* %s : %s\n' % (attr.name, attr_str_lines[0])
        else:
            text = '* %s : <None>\n' % attr.name
    return text

def dumpAttr(attr):
    """Format an attribute.

    :param attr: The attribute to print.
    :type attr: (anything goes)
    :return: String for the attribute.
    """
    if isinstance(attr, (NifFormat.Ref, NifFormat.Ptr)):
        ref = attr.get_value()
        if ref:
            if (hasattr(ref, "name")):
                return "<%s:%s:0x%08X>" % (ref.__class__.__name__,
                                           ref.name, id(attr))
            else:
                return "<%s:0x%08X>" % (ref.__class__.__name__,id(attr))
        else:
            return "<None>"
    elif isinstance(attr, list):
        return dumpArray(attr)
    elif isinstance(attr, NifFormat.NiObject):
        raise TypeError("cannot dump NiObject as attribute")
    elif isinstance(attr, NifFormat.byte):
        return tohex(attr.get_value(), 1)
    elif isinstance(attr, (NifFormat.ushort, NifFormat.short)):
        return tohex(attr.get_value(), 2)
    elif isinstance(attr, (NifFormat.int, NifFormat.uint)):
        return tohex(attr.get_value(), 4)
    elif isinstance(attr, (types.IntType, types.LongType)):
        return tohex(attr, 4)
    else:
        return str(attr)
    
class SpellDumpAll(NifSpell):
    """Dump the whole nif file."""

    SPELLNAME = "dump"

    def branchentry(self, branch):
        # dump it
        self.toaster.msg(dumpBlock(branch))
        # continue recursion
        return True

class SpellDumpTex(NifSpell):
    """Dump the texture and material info of all geometries."""

    SPELLNAME = "dump_tex"

    def branchinspect(self, branch):
        # stick to main tree nodes, and material and texture properties
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTexturingProperty,
                                   NifFormat.NiMaterialProperty))

    def branchentry(self, branch):
        if isinstance(branch, NifFormat.NiTexturingProperty):
            for textype in ('base', 'dark', 'detail', 'gloss', 'glow',
                            'bump_map', 'decal_0', 'decal_1', 'decal_2',
                            'decal_3'):
                if getattr(branch, 'has_%s_texture' % textype):
                    texdesc = getattr(branch,
                                      '%s_texture' % textype)
                    if texdesc.source:
                        if texdesc.source.use_external:
                            filename = texdesc.source.file_name
                        else:
                            filename = '(pixel data packed in file)'
                    else:
                        filename = '(no texture file)'
                    self.toaster.msg("[%s] %s" % (textype, filename))
            self.toaster.msg("apply mode %i" % branch.apply_mode)
            # stop recursion
            return False
        elif isinstance(branch, NifFormat.NiMaterialProperty):
            for coltype in ['ambient', 'diffuse', 'specular', 'emissive']:
                col = getattr(branch, '%s_color' % coltype)
                self.toaster.msg('%-10s %4.2f %4.2f %4.2f'
                                 % (coltype, col.r, col.g, col.b))
            self.toaster.msg('glossiness %f' % branch.glossiness)
            self.toaster.msg('alpha      %f' % branch.alpha)
            # stop recursion
            return False
        else:
            # keep looking for blocks of interest
            return True

class SpellHtmlReport(NifSpell):
    """Make a html report of selected blocks."""

    SPELLNAME = "dump_htmlreport"
    ENTITIES = { "\n": "<br/>" }

    @classmethod
    def toastentry(cls, toaster):
        # maps each block type to a list of reports for that block type
        toaster.reports_per_blocktype = {}
        # spell always applies
        return True

    def _branchinspect(self, branch):
        # enter every branch
        # (the base method is called in branch entry)
        return True
        
    def branchentry(self, branch):
        # check if this branch must be checked, if not, recurse further
        if not NifSpell._branchinspect(self, branch):
            return True
        blocktype = branch.__class__.__name__
        reports = self.toaster.reports_per_blocktype.get(blocktype)
        if not reports:
            # start a new report for this block type
            row = "<tr>"
            row += "<th>%s</th>" % "file" 
            row +=  "<th>%s</th>" % "id" 
            for attr in branch._get_filtered_attribute_list(data=self.data):
                row += ("<th>%s</th>"
                        % escape(attr.displayname, self.ENTITIES))
            row += "</tr>"
            reports = [row]
            self.toaster.reports_per_blocktype[blocktype] = reports
        
        row = "<tr>"
        row += "<td>%s</td>" % escape(self.stream.name)
        row += "<td>%s</td>" % escape("0x%08X" % id(branch), self.ENTITIES)
        for attr in branch._get_filtered_attribute_list(data=self.data):
            row += ("<td>%s</td>"
                    % escape(dumpAttr(getattr(branch, "_%s_value_"
                                              % attr.name)),
                             self.ENTITIES))
        row += "</tr>"
        reports.append(row)
        # keep looking for blocks of interest
        return True

    @classmethod
    def toastexit(cls, toaster):
        if toaster.reports_per_blocktype:
            rows = []
            rows.append( "<head>" )
            rows.append( "<title>Report</title>" )
            rows.append( "</head>" )
            rows.append( "<body>" )

            for blocktype, reports in toaster.reports_per_blocktype.iteritems():
                rows.append("<h1>%s</h1>" % blocktype)
                rows.append('<table border="1" cellspacing="0">')
                rows.append("\n".join(reports))
                rows.append("</table>")

            rows.append("</body>")

            cls.browser("\n".join(rows))
        else:
            toaster.msg('No Report Generated')

    @classmethod
    def browser(cls, htmlstr):
        """Display html in the default web browser without creating a
        temp file.
        
        Instantiates a trivial http server and calls webbrowser.open
        with a URL to retrieve html from that server.
        """    
        class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
            def do_GET(self):
                bufferSize = 1024*1024
                for i in xrange(0, len(htmlstr), bufferSize):
                    self.wfile.write(htmlstr[i:i+bufferSize])

        server = BaseHTTPServer.HTTPServer(('127.0.0.1', 0), RequestHandler)
        webbrowser.open('http://127.0.0.1:%s' % server.server_port)
        server.handle_request()           

class SpellExportPixelData(NifSpell):
    """Export embedded images as DDS files. If the toaster's
    ``--dryrun`` option is enabled, the image is written to a
    temporary file, otherwise, if no further path information is
    stored in the nif, it is written to
    ``<nifname>-pixeldata-<n>.dds``. If a path is stored in the nif,
    then the original file path is used.

    The ``--arg`` option is used to strip the folder part of the path
    and to replace it with something else (this is sometimes useful,
    such as in Bully nft files).

    The file extension is forced to ``.dds``.
    """

    SPELLNAME = "dump_pixeldata"

    def __init__(self, *args, **kwargs):
        NifSpell.__init__(self, *args, **kwargs)
        self.pixeldata_counter = 0
        """Increments on each pixel data block."""

    def datainspect(self):
        return self.inspectblocktype(NifFormat.ATextureRenderData)

    def branchinspect(self, branch):
        # stick to main tree nodes, and material and texture properties
        return isinstance(branch, (NifFormat.NiAVObject,
                                   NifFormat.NiTexturingProperty,
                                   NifFormat.NiSourceTexture,
                                   NifFormat.ATextureRenderData))

    def branchentry(self, branch):

        if (isinstance(branch, NifFormat.NiSourceTexture)
            and branch.pixel_data and branch.file_name):
            self.save_as_dds(branch.pixel_data, branch.file_name)
            return False
        elif isinstance(branch, NifFormat.ATextureRenderData):
            filename = "%s-pixeldata-%i" % (
                os.path.basename(self.stream.name),
                self.pixeldata_counter)
            self.save_as_dds(branch, filename)
            self.pixeldata_counter += 1
            return False
        else:
            # keep recursing
            return True

    @classmethod
    def get_toast_stream(cls, toaster, filename, test_exists=False):
        """We do not toast the original file, so stream construction
        is delegated to :meth:`get_toast_pixeldata_stream`.
        """
        if test_exists:
            return False
        else:
            return None

    @staticmethod
    def get_pixeldata_head_root(texture_filename):
        r"""Transform NiSourceTexture.file_name into something workable.

        >>> SpellExportPixelData.get_pixeldata_head_root("test.tga")
        ('', 'test')
        >>> SpellExportPixelData.get_pixeldata_head_root(r"textures\test.tga")
        ('textures', 'test')
        >>> SpellExportPixelData.get_pixeldata_head_root(
        ...     r"Z:\Bully\Temp\Export\Textures\Clothing\P_Pants1\P_Pants1_d.tga")
        ('z:/bully/temp/export/textures/clothing/p_pants1', 'p_pants1_d')
        """
        # note: have to use ntpath here so we can split correctly
        # nif convention always uses windows style paths
        head, tail = ntpath.split(texture_filename)
        root, ext = ntpath.splitext(tail)
        # for linux: make paths case insensitive by converting to lower case
        head = head.lower()
        root = root.lower()
        # XXX following is disabled because not all textures in Bully
        # XXX actually have this form; use "-a textures" for this game
        # make relative path for Bully SE
        #tmp1, tmp2, tmp3 = head.partition("\\bully\\temp\\export\\")
        #if tmp2:
        #    head = tmp3
        # for linux: convert backslash to forward slash
        head = head.replace("\\", "/")
        return (head, root) if root else ("", "image")

    def get_toast_pixeldata_stream(self, texture_filename):
        # dry run: no file name
        if self.toaster.options["dryrun"]:
            self.toaster.msg("saving as temporary file")
            return tempfile.TemporaryFile()
        # get head and root, and override head if requested
        head, root = self.get_pixeldata_head_root(texture_filename)
        if self.toaster.options["arg"]:
            head = self.toaster.options["arg"]
        # create path to file of the to be exported pixeldata
        toast_head = self.toaster.get_toast_head_root_ext(self.stream.name)[0]
        head = os.path.join(toast_head, head)
        if head:
            if not os.path.exists(head):
                self.toaster.msg("creating path %s" % head)
                os.makedirs(head)
        # create file
        filename = os.path.join(head, root) + ".dds"
        if self.toaster.options["resume"]:
            if os.path.exists(filename):
                self.toaster.msg("%s (already done)" % filename)
                return None
        self.toaster.msg("saving as %s" % filename)
        return open(filename, "wb")

    def save_as_dds(self, pixeldata, texture_filename):
        """Save pixeldata as dds file, using the specified filename."""
        self.toaster.msg("found pixel data (format %i)"
                         % pixeldata.pixel_format)
        try:
            stream = self.get_toast_pixeldata_stream(texture_filename)
            if stream:
                pixeldata.save_as_dds(stream)
        finally:
            if stream:
                stream.close()
