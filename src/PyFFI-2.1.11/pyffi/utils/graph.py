"""Base classes for organizing data (for instance to visualize data
with Qt, or to run hierarchical checks) in a global graph, and a
detail tree at each node of the global graph.

The classes defined here assume that data can be organized in two
stages: a global level which only shows 'top-level' objects
(i.e. large file blocks, chunks, and so on) as nodes and links between
the nodes via directed arcs, and a detail level which shows the
details of a top-level object, that is, the actual data they
contain.

:class:`DetailNode` implements the detail side of things. The
:class:`GlobalNode` class implements the global level, which does not show
any actual data, but only structure.

The global level forms a directed graph where the nodes are data
blocks and directed edges represent links from one block to
another.

This directed graph is assumed to have a spanning acyclic directed
subgraph, that is, a subgraph which contains all nodes of the original
graph, and which contains no cycles. This graph constitutes of those
edges which have the default edge type.

The :class:`pyffi.object_models.Data` class is the root node of
the graph. Recursing over all edges of default type of this node will
visit each node (possibly more than once) in a hierarchical order.

The base classes are roughly based on the TreeItem example in the Qt docs:
http://doc.trolltech.com/4.4/itemviews-simpletreemodel.html
"""

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

from itertools import repeat
from operator import itemgetter

class EdgeType(tuple):
    """Represents all possible edge types. By default, there are four
    types: any edge can be part of the acyclic graph or not, and can
    be active or not.

    The default edge type is active and acylic.
    """

    def __new__(cls, active=True, acyclic=True):
        return tuple.__new__(cls, (active, acyclic))

    active = property(itemgetter(0))
    acyclic = property(itemgetter(1))

class EdgeFilter(tuple):
    """A simple filter for edges. The default filter only checks the edge's
    active and acyclic attributes, and accepts them if both are ``True``.
    """
    def __new__(cls, active_filter=True, acyclic_filter=True):
        return tuple.__new__(cls, (active_filter, acyclic_filter))
    
    active_filter = property(itemgetter(0))
    acyclic_filter = property(itemgetter(1))

    def accept(self, edge_type):
        if not(self.active_filter is None):
            if edge_type.active != self.active_filter:
                return False
        if not(self.acyclic_filter is None):
            if edge_type.acyclic != self.acyclic_filter:
                return False

class DetailNode(object):
    """A node of the detail tree which can have children.

    If the data must be editable, also derive the class from one of
    the delegate classes defined in :mod:`pyffi.object_models.editable`,
    and make sure that the get_value and set_value functions are
    implemented.
    """

    def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
        """Generator which yields all children of this item in the
        detail view (by default, all acyclic and active ones).

        Override this method if the node has children.

        :param edge_filter: The edge type to include.
        :type edge_filter: :class:`EdgeFilter` or ``type(None)``
        :return: Generator for detail tree child nodes.
        :rtype: generator yielding :class:`DetailNode`\ s
        """
        return (dummy for dummy in ())

    def get_detail_child_names(self, edge_filter=EdgeFilter()):
        """Generator which yields all child names of this item in the detail
        view.

        Override this method if the node has children.

        :return: Generator for detail tree child names.
        :rtype: generator yielding ``str``\ s
        """
        return (dummy for dummy in ())

    def get_detail_child_edge_types(self, edge_filter=EdgeFilter()):
        """Generator which yields all edge types of this item in the
        detail view, one edge type for each child.

        Override this method if you rely on more than one edge type.
        """
        return repeat(EdgeType())

    def get_detail_display(self):
        """Object used to display the instance in the detail view.

        Override this method if the node has data to display in the detail view.

        :return: A string that can be used to display the instance.
        :rtype: ``str``
        """
        return ""

    def get_detail_iterator(self, edge_filter=EdgeFilter()):
        """Iterate over self, all children, all grandchildren, and so
        on (only given edge type is followed). Do not override.
        """
        yield self
        for child in self.get_detail_child_nodes(edge_filter=edge_filter):
            for branch in child.get_detail_iterator(edge_filter=edge_filter):
                yield branch

    def replace_global_node(self, oldnode, newnode, edge_filter=EdgeFilter()):
        """Replace a particular branch in the graph."""
        raise NotImplementedError

class GlobalNode(DetailNode):
    """A node of the global graph."""

    def get_global_display(self):
        """Very short summary of the data of this global branch for display
        purposes. Override this method.

        :return: A string.
        """
        return ""
        # possible implementation:
        #return self.name if hasattr(self, "name") else ""

    def get_global_child_nodes(self, edge_filter=EdgeFilter()):
        """Generator which yields all children of this item in the
        global view, of given edge type (default is edges of type 0).

        Override this method.

        :return: Generator for global node children.
        """
        return (dummy for dummy in ())

    def get_global_child_edge_types(self, edge_filter=EdgeFilter()):
        """Generator which yields all edge types of this item in the
        global view, one edge type for each child.

        Override this method if you rely on non-default edge types.
        """
        return repeat(EdgeType())

    def get_global_iterator(self, edge_filter=EdgeFilter()):
        """Iterate over self, all children, all grandchildren, and so
        on (only given edge_filter is followed). Do not override.
        """
        yield self
        for child in self.get_global_child_nodes(edge_filter=edge_filter):
            for branch in child.get_global_iterator(edge_filter=edge_filter):
                yield branch
