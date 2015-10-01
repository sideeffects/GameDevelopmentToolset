"""Implements base class for basic types."""

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

from pyffi.utils.graph import DetailNode

class BasicBase(DetailNode):
    """Base class from which all basic types are derived.

    The BasicBase class implements the interface for basic types.
    All basic types are derived from this class.
    They must override read, write, get_value, and set_value.

    >>> import struct
    >>> class UInt(BasicBase):
    ...     def __init__(self, template = None, argument = 0):
    ...         self.__value = 0
    ...     def read(self, version = None, user_version = None, f = None,
    ...              link_stack = [], argument = None):
    ...         self.__value, = struct.unpack('<I', f.read(4))
    ...     def write(self, version = None, user_version = None, f = None,
    ...               block_index_dct = {}, argument = None):
    ...         f.write(struct.pack('<I', self.__value))
    ...     def get_value(self):
    ...         return self.__value
    ...     def set_value(self, value):
    ...         self.__value = int(value)
    >>> x = UInt()
    >>> x.set_value('123')
    >>> x.get_value()
    123
    >>> class Test(BasicBase): # bad: read, write, get_value, and set_value are
    ...                        # not implemented
    ...     pass
    >>> x = Test() # doctest: +ELLIPSIS
    >>> x.set_value('123') # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    NotImplementedError
    """

    _is_template = False # is it a template type?
    _has_links = False # does the type contain a Ref or a Ptr?
    _has_refs = False # does the type contain a Ref?
    _has_strings = False # does the type contain a string?
    arg = None # default argument

    def __init__(self, template = None, argument = None, parent = None):
        """Initializes the instance.

        :param template: type used as template
        :param argument: argument used to initialize the instance
            (see the Struct class).
        :param parent: The parent of this instance, that is, the instance this
            instance is an attribute of."""
        # parent disabled for performance
        #self._parent = weakref.ref(parent) if parent else None
        pass

    # string representation
    def __str__(self):
        """Return string representation."""
        return str(self.get_value())

    def read(self, stream, data):
        """Read object from file."""
        raise NotImplementedError

    def write(self, stream, data):
        """Write object to file."""
        raise NotImplementedError

    def fix_links(self, data):
        """Fix links. Called when all objects have been read, and converts
        block indices into blocks."""
        pass

    def get_links(self, data=None):
        """Return all links referred to in this object."""
        return []

    def get_strings(self, data):
        """Return all strings used by this object."""
        return []

    def get_refs(self, data=None):
        """Return all references (excluding weak pointers) used by this
        object."""
        return []

    def get_value(self):
        """Return object value."""
        raise NotImplementedError

    def set_value(self, value):
        """Set object value."""
        raise NotImplementedError

    def get_size(self, data=None):
        """Returns size of the object in bytes."""
        raise NotImplementedError

    def get_hash(self, data=None):
        """Returns a hash value (an immutable object) that can be used to
        identify the object uniquely."""
        raise NotImplementedError

    def replace_global_node(self, oldbranch, newbranch, **kwargs):
        """Replace a given branch."""
        pass

    #
    # user interface functions come next
    # these functions are named after similar ones in the TreeItem example
    # at http://doc.trolltech.com/4.3/itemviews-simpletreemodel.html
    #

    # DetailNode

    def get_detail_display(self):
        """Return an object that can be used to display the instance."""
        return str(self.get_value())

    # editor functions: default implementation assumes that the value is
    # also suitable for an editor; override if not

    def get_editor_value(self):
        """Return value suitable for editor."""
        return self.get_value()

    def set_editor_value(self, editorvalue):
        """Set value from editor value."""
        return self.set_value(editorvalue)

