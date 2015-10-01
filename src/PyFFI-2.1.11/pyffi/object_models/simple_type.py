"""Defines the base class for simple types."""

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

from pyffi.object_models.any_type import AnyType

class _MetaSimpleType(type):
    """This metaclass binds the get_value and set_value methods to the
    value property. We need a metaclass for this because properties are
    non-polymorphic. Further reading:
    http://stackoverflow.com/questions/237432/python-properties-and-inheritance
    http://requires-thinking.blogspot.com/2006/03/note-to-self-python-properties-are-non.html
    """
    def __init__(cls, name, bases, dct):
        # call base class constructor
        super(_MetaSimpleType, cls).__init__(name, bases, dct)
        # add value property
        cls.value = property(cls.get_value, cls.set_value,
                             None, cls.value.__doc__)

class SimpleType(AnyType):
    """Base class from which all simple types are derived. Simple
    types contain data which is not divided further into smaller pieces,
    and that can represented efficiently by a (usually native) Python type,
    typically ``int``, ``float``, or ``str``.

    A brief example of usage:

    >>> class Short(SimpleType):
    ...     def __init__(self):
    ...         # for fun, let default value be 3
    ...         self._value = 3
    ...     def set_value(self, value):
    ...         # check type
    ...         if not isinstance(value, int):
    ...             raise TypeError("Expected int but got %s."
    ...                             % value.__class__.__name__)
    ...         # check range
    ...         if value < -0x8000 or value > 0x7fff:
    ...             raise ValueError("Value %i out of range." % value)
    ...         self._value = value
    >>> test = Short()
    >>> print(test)
    3
    >>> test.value = 255
    >>> print(test)
    255
    >>> test.value = 100000 # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> test.value = "hello world" # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    TypeError: ...

    Also override :meth:`read` and :meth:`write` if you wish to read and write data
    of this type, and :meth:`is_interchangeable` if you wish to declare data as
    equivalent.
    """

    __metaclass__ = _MetaSimpleType

    # added here for documentation purposes - actually set in
    # metaclass
    @property
    def value(self):
        """A property which wraps the actual data. This property
        always calls :meth:`set_value` to assign the value, and ensures
        that the value is valid (type, range, ...). Unless you know
        what you are doing, always use the `value` property to change
        the data.
        """
        return None

    _value = None
    """The data."""

    def __str__(self):
        """String representation. This implementation is simply a wrapper
        around ``str`` on :attr:`_value`.

        :return: String representation.
        :rtype: ``str``
        """
        return self._value.__str__()

    def get_value(self):
        """Return the stored value.

        :return: The stored value.
        :rtype: Whatever is appropriate.
        """
        return self._value

    def set_value(self, value):
        """Set stored value. Override this method to enable validation
        (type checking, range checking, and so on).

        :param value: The value to store.
        :type value: Whatever is appropriate.
        """
        self._value = value

    # AnyType

    def is_interchangeable(self, other):
        """This checks for object identity of the value."""
        return isinstance(other, SimpleType) and (self._value is other._value)

    # DetailNode

    def get_detail_display(self):
        """Display string for the detail tree. This implementation is simply
        a wrapper around C{self.:attr:`_value`.__str__()}.

        :return: String representation.
        :rtype: ``str``
        """
        return self._value.__str__()
