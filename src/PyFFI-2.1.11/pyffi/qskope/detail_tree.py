# --------------------------------------------------------------------------
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
# --------------------------------------------------------------------------

from itertools import izip

from pyffi.utils.graph import DetailNode, EdgeType, EdgeFilter

class DetailTreeItemData(object):
    """Stores all data used in the detail view.

    :ivar node: The node of the item.
    :type node: :class:`DetailNode`
    :ivar name: The name of the node (this is usually not stored in the node).
    :type name: ``str``
    """
    def __init__(self, node=None, name=None):
        if not isinstance(node, DetailNode):
            raise TypeError("node must be DetailNode instance")
        if not isinstance(name, (type(None), basestring)):
            raise TypeError("name must be None or string instance")
        self.node = node
        self.name = name

    # convenience functions, these are used internally by QSkope

    @property
    def display(self):
        return self.node.get_detail_display()

    @property
    def typename(self):
        return self.node.__class__.__name__

class DetailTreeItem(object):
    """Stores all internal information to vizualize :class:`DetailNode`\ s in a
    tree view.

    :ivar data: The item data.
    :type data: :class:`DetailTreeItemData`
    :ivar parent: The parent of the node.
    :type parent: ``type(None)`` or :class:`DetailTreeItem`
    :ivar children: The children of the node.
    :type children: ``list`` of :class:`DetailTreeItem`
    :ivar row: The row number of this node, as child.
    :type row: ``int``
    :ivar edge_type: The type of edge from the parent of this node to itself.
    :type edge_type: :class:`EdgeType`
    """
    def __init__(self, data=None, parent=None, row=0, edge_type=EdgeType(),
                 edge_filter=EdgeFilter()):
        """Initialize the node tree hierarchy from the given data."""
        if not isinstance(data, DetailTreeItemData):
            raise TypeError(
                "data must be a DetailTreeItemData instance")
        if not isinstance(parent, (type(None), DetailTreeItem)):
            raise TypeError(
                "parent must be either None or a DetailTreeItem instance")
        if not isinstance(edge_type, EdgeType):
            raise TypeError("edge_type must be EdgeType instance")
        self.data = data
        self.parent = parent
        self.row = row
        self.edge_type = edge_type
        self.children = [
            DetailTreeItem(
                data=DetailTreeItemData(node=childnode, name=childname),
                parent=self,
                row=childrow,
                edge_type=child_edge_type)
            for (childrow, (childnode, childname, child_edge_type))
            in enumerate(izip(
                data.node.get_detail_child_nodes(edge_filter=edge_filter),
                data.node.get_detail_child_names(edge_filter=edge_filter),
                data.node.get_detail_child_edge_types(edge_filter=edge_filter)))]
