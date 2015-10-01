"""Defines base class for arrays of data."""

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

from pyffi.object_models.any_type import AnyType
import pyffi.object_models.simple_type
from pyffi.utils.graph import EdgeFilter

class ValidatedList(list):
    """Abstract base class for lists whose items can be validated (for
    instance, for type checks).
    """
    def __init__(self, *args, **kwargs):
        """Initialize empty list."""
        list.__init__(self, *args, **kwargs)
        for item in list.__iter__(self):
            self.validate(item)

    @classmethod
    def validate(cls, item):
        """Checks that the item can be added to the list."""
        raise NotImplementedError

    def __setitem__(self, index, item):
        """Set item at given index."""
        # set the new item
        self.validate(item)
        list.__setitem__(self, index, item)

    def append(self, item):
        """Validate item and append to list."""
        self.validate(item)
        list.append(self, item)

    def extend(self, other):
        """Validate items and extend list."""
        # make a list copy of other
        otherlist = list(other)
        # validate each item of other
        for item in otherlist:
            self.validate(item)
        # extend
        list.extend(self, otherlist)

    def insert(self, index, item):
        """Validate item and insert."""
        self.validate(item)
        list.insert(self, index, item)

class AnyArray(ValidatedList, AnyType):
    """Abstract base class for all array types.

    @cvar _MAXSTR: Maximum number of elements to write in the L{__str__} method.
    :type _MAXSTR: ``int``
    """

    _MAXSTR = 16

    def is_interchangeable(self, other):
        """Check if array's are interchangeable."""
        # compare classes
        if not(self.__class__ is other.__class__):
            return False
        # compare lengths
        if list.__len__(self) != list.__len__(other):
            return False
        # compare elements
        for item, otheritem in izip(list.__iter__(self), list.__iter__(other)):
            if not item.is_interchangeable(otheritem):
                return False
        # all elements are interchangeable, so the array is as well
        return True

    def __str__(self):
        """String representation.

        :return: String representation.
        :rtype: ``str``
        """
        # TODO use getDetailTypeName
        result = "%s array:\n" % self.ItemType.__name__
        more = False
        for itemnum, item in enumerate(self):
            if itemnum >= self._MAXSTR:
                more = True
                break
            result += "  [%02i] %s\n" % (itemnum, item)
        if more:
            result += ("  ...  (%i more following)\n"
                       % (len(self) - self._MAXSTR))
        return result

    def get_detail_child_nodes(self, edge_filter=EdgeFilter()):
        return list.__iter__(self)

    def get_detail_child_names(self, edge_filter=EdgeFilter()):
        return ("[%i]" % i for i in xrange(list.__len__(self)))

class MetaUniformArray(type):
    """Metaclass for L{UniformArray}. Checks that
    L{ItemType<UniformArray.ItemType>} is an
    L{AnyType<pyffi.object_models.any_type.AnyType>} subclass.
    """
    def __init__(cls, name, bases, dct):
        """Initialize array type."""
        # create the class
        super(MetaUniformArray, cls).__init__(name, bases, dct)
        # check type of elements
        if not issubclass(cls.ItemType, AnyType):
            raise TypeError("array ItemType must be an AnyType subclass")

class UniformArray(AnyArray):
    """Wrapper for array with elements of the same type; this type must be
    a subclass of L{pyffi.object_models.any_type.AnyType}.

    >>> from pyffi.object_models.simple_type import SimpleType
    >>> class MyInt(SimpleType):
    ...     # in practice one would implement some sort of type checking
    ...     # for this example we keep it simple
    ...     def __init__(self, value=0):
    ...         self._value = value
    >>> class ListOfInts(UniformArray):
    ...     ItemType = MyInt
    >>> testlist = ListOfInts()
    >>> testlist.append(MyInt(value=20))
    >>> testlist.extend([MyInt(value=val) for val in range(2, 10, 2)])
    >>> print(testlist)
    MyInt array:
      [00] 20
      [01] 2
      [02] 4
      [03] 6
      [04] 8
    <BLANKLINE>
    >>> [item.value for item in testlist[::-2]]
    [8, 4, 20]

    @cvar ItemType: Type of the elements of this array.
    :type ItemType: L{pyffi.object_models.any_type.AnyType}
    """

    __metaclass__ = MetaUniformArray
    ItemType = AnyType

    @classmethod
    def validate(cls, item):
        """Check if item can be added."""
        if not item.__class__ is cls.ItemType:
            raise TypeError("item has incompatible type (%s, not %s)"
                            % (item.__class__.__name__,
                               cls.ItemType.__name__))

class MetaUniformSimpleArray(type):
    """Metaclass for L{UniformSimpleArray}. Checks that
    L{ItemType<UniformSimpleArray.ItemType>} is an
    L{SimpleType<pyffi.object_models.simple_type.SimpleType>} subclass.
    """
    def __init__(cls, name, bases, dct):
        """Initialize array type."""
        # create the class
        super(MetaUniformSimpleArray, cls).__init__(name, bases, dct)
        # check type of elements
        if not issubclass(cls.ItemType,
                          pyffi.object_models.simple_type.SimpleType):
            raise TypeError("array ItemType must be a SimpleType subclass")

class UniformSimpleArray(AnyArray):
    """Base class for array's with direct access to values of simple items."""

    __metaclass__ = MetaUniformSimpleArray
    ItemType = pyffi.object_models.simple_type.SimpleType

    def __getitem__(self, index):
        # using list base method for speed
        return list.__getitem__(self, index).value

    def __setitem__(self, index, value):
        # using list base method to skip validation
        list.__getitem__(self, index).value = value

    def __iter__(self):
        return (item.value for item in list.__iter__(self))

    def __contains__(self, value):
        return value in (item.value for item in list.__iter__(self))

    def append(self, value):
        # using list base method to skip validation
        list.append(self, self.ItemType(value))

    def count(self, value):
        """@warning: not efficient."""
        # count in list of values
        list(self.__iter__()).count(value)

    def extend(self, other):
        """Extend list."""
        # using list base method to skip validation
        list.extend(self, (self.ItemType(value) for value in other))

    def index(self, value):
        """@warning: not efficient."""
        return list(self.__iter__()).index(value)

    def insert(self, index, value):
        """Insert."""
        # using list base method for speed
        list.insert(self, index, self.ItemType(value))

    def pop(self, index=-1):
        return list.pop(self, index).value

    def remove(self, value):
        """@warning: not efficient."""
        self.list.pop(self, self.index(value))
