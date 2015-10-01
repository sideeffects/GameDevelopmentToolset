"""The DetailModel module defines a model to display the details of
StructBase, Array, and BasicBase instances."""

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

from PyQt4 import QtCore

from pyffi.utils.graph import EdgeFilter, GlobalNode
from pyffi.qskope.detail_tree import DetailTreeItem, DetailTreeItemData

# implementation references:
# http://doc.trolltech.com/4.3/model-view-programming.html
# http://doc.trolltech.com/4.3/model-view-model-subclassing.html
class DetailModel(QtCore.QAbstractItemModel):
    """General purpose model for QModelIndexed access to pyffi data structures
    such as StructBase, Array, and BasicBase instances."""
    # column definitions
    NUM_COLUMNS = 3
    COL_NAME  = 0
    COL_TYPE  = 1
    COL_VALUE = 2

#    def __init__(self, parent = None, block = None, refnumber_dict = None):
#        """Initialize the model to display the given block. The refnumber_dict
#        dictionary is used to handle references in the block."""
#        QtCore.QAbstractItemModel.__init__(self, parent)
#        # this list stores the blocks in the view
#        # is a list of NiObjects for the nif format, and a list of Chunks for
#        # the cgf format
#        self.block = block
#        self.refNumber = refnumber_dict if not refnumber_dict is None else {}

    def __init__(self, parent=None, globalnode=None, globalmodel=None,
                 edge_filter=EdgeFilter()):
        """Initialize the model to display the given global node in the
        detail tree. We also need a reference to the global model to
        resolve node references.
        """
        QtCore.QAbstractItemModel.__init__(self, parent)
        self.root_item = DetailTreeItem(
            data=DetailTreeItemData(node=globalnode),
            edge_filter=EdgeFilter())
        self.globalmodel = globalmodel

    def flags(self, index):
        """Return flags for the given index: all indices are enabled and
        selectable."""
        if not index.isValid():
            return QtCore.Qt.ItemFlags()
        # all items are enabled and selectable
        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        # determine whether item value can be set
        if index.column() == self.COL_VALUE:
            try:
                index.internalPointer().data.node.get_value()
                # TODO: find more clever system
            except AttributeError:
                pass
            except NotImplementedError:
                pass
            else:
                flags |= QtCore.Qt.ItemIsEditable
        return QtCore.Qt.ItemFlags(flags)

    def data(self, index, role):
        """Return the data of model index in a particular role. Only
        QtCore.Qt.DisplayRole is implemented.
        """
        # check if the index is valid
        # check if the role is supported
        if not index.isValid() or role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        # get the data for display
        item = index.internalPointer()

        # the name column
        if index.column() == self.COL_NAME:
            return QtCore.QVariant(item.data.name)

        # the type column
        elif index.column() == self.COL_TYPE:
            return QtCore.QVariant(item.data.typename)

        # the value column
        elif index.column() == self.COL_VALUE:
            # get display element
            display = item.data.display
            if isinstance(display, GlobalNode):
                # reference
                blocknum = self.globalmodel.index_dict[display]
                if (not hasattr(display, "name") or not display.name):
                    return QtCore.QVariant(
                        "%i [%s]" % (blocknum, display.__class__.__name__))
                else:
                    return QtCore.QVariant(
                        "%i (%s)" % (blocknum, display.name))
            elif isinstance(display, basestring):
                # regular string
                if len(display) > 32:
                    display = display[:32] + "..."
                return QtCore.QVariant(
                    display.replace("\n", " ").replace("\r", " "))
            else:
                raise TypeError("%s: do not know how to display %s"
                                % (item.data.name, display.__class__.__name__))

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
            elif section == self.COL_VALUE:
                return QtCore.QVariant("Value")
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Calculate a row count for the given parent index."""
        if not parent.isValid():
            # top level: one row for each attribute
            return len(self.root_item.children)
        else:
            # get the parent child count
            return len(parent.internalPointer().children)

    def columnCount(self, parent=QtCore.QModelIndex()):
        """Return column count."""
        # column count is constant everywhere
        return self.NUM_COLUMNS

    def index(self, row, column, parent):
        """Create an index to item (row, column) of object parent."""
        # check if the parent is valid
        if not parent.isValid():
            # parent is not valid, so we need a top-level object
            # return the row'th attribute
            item = self.root_item.children[row]
        else:
            # parent is valid, so we need to go get the row'th attribute
            # get the parent pointer
            item = parent.internalPointer().children[row]
        return self.createIndex(row, column, item)

    def parent(self, index):
        """Calculate parent of a given index."""
        # get parent structure
        parent_item = index.internalPointer().parent
        # if parent's parent is None, then index must be a top
        # level object, so return invalid index
        if parent_item.parent is None:
            return QtCore.QModelIndex()
        # if parent's parent is not None, then it must be member of
        # some deeper nested structure, so calculate the row as usual
        else:
            return self.createIndex(parent_item.row, 0, parent_item)

    def setData(self, index, value, role):
        """Set data of a given index from given QVariant value. Only
        QtCore.Qt.EditRole is implemented.
        """
        if role == QtCore.Qt.EditRole:
            # fetch the current data, as a regular Python type
            node = index.internalPointer().data.node
            currentvalue = node.get_value()
            # transform the QVariant value into the right class
            if isinstance(currentvalue, (int, long)):
                # use long type to work around QVariant(0xffffffff).toInt() bug
                pyvalue, ok = value.toLongLong()
            elif isinstance(currentvalue, float):
                pyvalue, ok = value.toDouble()
            elif isinstance(currentvalue, basestring):
                pyvalue = str(value.toString())
                ok = True
            elif isinstance(currentvalue, bool):
                pyvalue, ok = value.toBool()
            else:
                # type not supported
                return False
            # check if conversion worked
            if not ok:
                return False
            # set the value (EditRole, so use set_editor_value, not set_value)
            node.set_editor_value(pyvalue)
            # tell everyone that the data has changed
            self.emit(QtCore.SIGNAL('dataChanged(QModelIndex, QModelIndex)'),
                                    index, index)
            return True
        # all other cases: failed
        return False
