"""Defines base class for any type that stores mutable data
which is readable and writable, and can check for exchangeable
alternatives.
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

import pyffi.utils.graph

class AnyType(pyffi.utils.graph.DetailNode):
    """Abstract base class from which all types are derived."""

    def read(self, stream):
        """Read object from file.

        :param stream: The stream to read from.
        :type stream: ``file``
        """
        raise NotImplementedError

    def write(self, stream):
        """Write object to file.

        :param stream: The stream to write to.
        :type stream: ``file``
        """
        raise NotImplementedError

    def is_interchangeable(self, other):
        """Returns ``True`` if objects are interchangeable, that is,
        "close" enough to each other so they can be considered equal
        for practical purposes. This is useful for instance when comparing
        data and trying to remove duplicates.

        This default implementation simply checks for object identity.

        >>> x = AnyType()
        >>> y = AnyType()
        >>> x.is_interchangeable(y)
        False
        >>> x.is_interchangeable(x)
        True

        :return: ``True`` if objects are close, ``False`` otherwise.
        :rtype: ``bool``
        """
        return self is other

    def __hash__(self):
        """AnyType objects are mutable, so raise type error on hash
        calculation, as they cannot be safely used as dictionary keys.
        """
        raise TypeError("%s objects are unhashable" % self.__class__.__name__)
