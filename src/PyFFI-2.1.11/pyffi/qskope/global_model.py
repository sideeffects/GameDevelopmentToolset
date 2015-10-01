"""The GlobalModel module defines a model to display the structure of a file
built from StructBase instances possibly referring to one another."""

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

from UserDict import DictMixin

from PyQt4 import QtGui, QtCore

from pyffi.utils.graph import EdgeFilter
from pyffi.qskope.global_tree import GlobalTreeItemData, GlobalTreeItem

# implementation references:
# http://doc.trolltech.com/4.3/model-view-programming.html
# http://doc.trolltech.com/4.3/model-view-model-subclassing.html
class GlobalModel(QtCore.QAbstractItemModel):
    """General purpose model for QModelIndexed access to data loaded with
    pyffi."""
    # column definitions
    NUM_COLUMNS = 3
    COL_TYPE = 0
    COL_NUMBER = 2
    COL_NAME = 1

    class IndexDict(DictMixin):
        def __init__(self):
            self.clear()

        def __getitem__(self, key):
            try:
                return self.data[id(key)]
            except KeyError:
                index = self.free_indices[-1]
                self.data[id(key)] = index
                if len(self.free_indices) == 1:
                    self.free_indices[0] += 1
                else:
                    self.free_indices.pop()

        def __delitem__(self, key):
            # index becomes available
            self.free_indices.append(self.data[id(key)])
            # remove it
            del self.data[id(key)] 

        def clear(self):
            # all indices larger than the first element
            # are free as well
            self.free_indices = [0]
            self.data = {}

    def __init__(self, parent=None, globalnode=None, edge_filter=EdgeFilter()):
        """Initialize the model to display the given data."""
        QtCore.QAbstractItemModel.__init__(self, parent)
        # set up the tree
        self.root_item = GlobalTreeItem(
            data=GlobalTreeItemData(node=globalnode),
            edge_filter=edge_filter)
        # set up the index dictionary
        self.index_dict = self.IndexDict()
        self.updateIndexDict(self.root_item)

    def updateIndexDict(self, item):
        self.index_dict[item.data.node]
        for child_item in item.children:
            self.updateIndexDict(child_item)
            

    def flags(self, index):
        """Return flags for the given index: all indices are enabled and
        selectable."""
        # all items are selectable
        # they are enabled if their edge_type is active
        if not index.isValid():
            return QtCore.Qt.ItemFlags()
        item = index.internalPointer()
        if item.edge_type.active:
            flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            flags = QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemFlags(flags)

    def data(self, index, role):
        """Return the data of model index in a particular role."""
        # check if the index is valid
        # check if the role is supported
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        # get the data for display
        data = index.internalPointer().data

        # the type column
        if index.column() == self.COL_TYPE:
            return QtCore.QVariant(data.typename)
        elif index.column() == self.COL_NAME:
            return QtCore.QVariant(data.display)
        elif index.column() == self.COL_NUMBER:
            return QtCore.QVariant(self.index_dict[data.node])

        # other colums: invalid
        else:
            return QtCore.QVariant()

    def headerData(self, section, orientation, role):
        """Return header data."""
        if (orientation == QtCore.Qt.Horizontal
            and role == QtCore.Qt.DisplayRole):
            if section == self.COL_TYPE:
                return QtCore.QVariant("Type")
            elif section == self.COL_NAME:
                return QtCore.QVariant("Name")
            elif section == self.COL_NUMBER:
                return QtCore.QVariant("#")
        return QtCore.QVariant()

    def rowCount(self, parent = QtCore.QModelIndex()):
        """Calculate a row count for the given parent index."""
        if not parent.isValid():
            return 1
        else:
            # get the parent child count = number of references
            return len(parent.internalPointer().children)

    def columnCount(self, parent = QtCore.QModelIndex()):
        """Return column count."""
        # column count is constant everywhere
        return self.NUM_COLUMNS

    def index(self, row, column, parent):
        """Create an index to item (row, column) of object parent."""
        # check if the parent is valid
        if not parent.isValid():
            # parent is not valid, so we need a top-level object
            # return the index with row'th block as internal pointer
            item = self.root_item
        else:
            # parent is valid, so we need to go get the row'th reference
            # get the parent pointer
            item = parent.internalPointer().children[row]
        return self.createIndex(row, column, item)

    def parent(self, index):
        """Calculate parent of a given index."""
        # get parent structure
        parent_item = index.internalPointer().parent
        # if parent's parent is None, then index must be a top
        # level object, so return invalid index
        if parent_item is None:
            return QtCore.QModelIndex()
        # if parent's parent is not None, then it must be member of
        # some deeper nested structure, so calculate the row as usual
        else:
            return self.createIndex(parent_item.row, 0, parent_item)
