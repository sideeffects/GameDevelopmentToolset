"""
:mod:`pyffi.object_models` --- File format description engines
==============================================================

.. warning::

   The documentation of this module is very incomplete.

This module bundles all file format object models. An object model
is a group of classes whose instances can hold the information
contained in a file whose format is described in a particular way
(xml, xsd, and possibly others).

..
  There is a strong distinction between types that contain very specific
  simple data (SimpleType) and more complex types that contain groups of
  simple data (ComplexType, with its descendants StructType for named
  lists of objects of different type and ArrayType for indexed lists of
  objects of the same type).
  
  The complex types are generic in that they can be instantiated using
  metadata (i.e. data describing the structure of the actual file data)
  from xml, xsd, or any other file format description.
  
  For the simple types there are specific classes implementing access to
  these data types. Typical implementations are present for integers,
  floats, strings, and so on. Some simple types may also be derived from
  already implemented simple types, if the metadata description allows
  this.

.. autoclass:: MetaFileFormat
   :show-inheritance:
   :members:

.. autoclass:: FileFormat
   :show-inheritance:
   :members:
"""

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

import codecs
import logging
import os.path # os.path.altsep
import re # compile
import sys # version_info

import pyffi.utils
import pyffi.utils.graph


class MetaFileFormat(type):
    """This metaclass is an abstract base class for transforming
    a file format description into classes which can be directly used to
    manipulate files in this format.

    A file format is implemented as a particular class (a subclass of
    :class:`FileFormat`) with class members corresponding to different
    (bit)struct types, enum types, basic types, and aliases.
    """

    @staticmethod
    def openfile(filename, filepaths=None, encoding=None):
        """Find *filename* in given *filepaths*, and open it. Raises
        ``IOError`` if file cannot be opened.

        :param filename: The file to open.
        :type filename: ``str``
        :param filepaths: List of paths where to look for the file.
        :type filepaths: ``list`` of ``str``\ s
        """

        def open_with_encoding(fn):
            if encoding is None:
                return open(fn)
            else:
                return codecs.open(fn, encoding=encoding)

        if not filepaths:
            return open_with_encoding(filename)
        else:
            for filepath in filepaths:
                if not filepath:
                    continue
                try:
                    return open_with_encoding(os.path.join(filepath, filename))
                except IOError:
                    continue
                break
            else:
                raise IOError(
                    "'%s' not found in any of the directories %s"
                    % (filename, filepaths))


class FileFormat(object):
    """This class is the base class for all file formats. It implements
    a number of useful functions such as walking over directory trees
    (:meth:`walkData`) and a default attribute naming function
    (:meth:`name_attribute`).
    It also implements the base class for representing file data
    (:class:`FileFormat.Data`).
    """

    RE_FILENAME = None
    """Override this with a regular expression (the result of a ``re.compile``
    call) for the file extension of the format you are implementing.
    """

    ARCHIVE_CLASSES = []
    """Override this with a list of archive formats that may contain
    files of the format.
    """

    # precompiled regular expressions, used in name_parts

    _RE_NAME_SEP = re.compile('[_\W]+')
    """Matches seperators for splitting names."""
    
    _RE_NAME_DIGITS = re.compile('([0-9]+)|([a-zA-Z]+)')
    """Matches digits or characters for splitting names."""

    _RE_NAME_CAMEL = re.compile('([A-Z][a-z]*)|([a-z]+)')
    """Finds components of camelCase and CamelCase names."""

    _RE_NAME_LC = re.compile('[a-z]')
    """Matches a lower case character."""

    _RE_NAME_UC = re.compile('[A-Z]')
    """Matches an upper case character."""

    # override this with the data instance for this format
    class Data(pyffi.utils.graph.GlobalNode):
        """Base class for representing data in a particular format.
        Override this class to implement reading and writing.
        """

        _byte_order = '<'
        """Set to '<' for little-endian, and '>' for big-endian."""

        version = None
        """Version of the data."""

        user_version = None
        """User version (additional version field) of the data."""

        def inspect(self, stream):
            """Quickly checks whether the stream appears to contain
            data of a particular format. Resets stream to original position.
            Call this function if you simply wish to check that a file is
            of a particular format without having to parse it completely.

            Override this method.

            :param stream: The file to inspect.
            :type stream: file
            :return: ``True`` if stream is of particular format, ``False``
                otherwise.
            """
            raise NotImplementedError

        def read(self, stream):
            """Read data of particular format from stream.
            Override this method.

            :param stream: The file to read from.
            :type stream: ``file``
            """
            raise NotImplementedError

        def write(self, stream):
            """Write data of particular format to stream.
            Override this method.

            :param stream: The file to write to.
            :type stream: ``file``
            """
            raise NotImplementedError

    @staticmethod
    def version_number(version_str):
        """Converts version string into an integer.
        This default implementation simply returns zero at all times,
        and works for formats that are not versioned.

        Override for versioned formats.

        :param version_str: The version string.
        :type version_str: ``str``
        :return: A version integer.
        """
        return 0

    @classmethod
    def name_parts(cls, name):
        """Intelligently split a name into parts:

        * first, split at non-alphanumeric characters
        * next, seperate digits from characters
        * finally, if some part has mixed case, it must be
          camel case so split it further at upper case characters

        >>> FileFormat.name_parts("hello_world")
        ['hello', 'world']
        >>> FileFormat.name_parts("HELLO_WORLD")
        ['HELLO', 'WORLD']
        >>> FileFormat.name_parts("HelloWorld")
        ['Hello', 'World']
        >>> FileFormat.name_parts("helloWorld")
        ['hello', 'World']
        >>> FileFormat.name_parts("xs:NMTOKEN")
        ['xs', 'NMTOKEN']
        >>> FileFormat.name_parts("xs:NCName")
        ['xs', 'N', 'C', 'Name']
        >>> FileFormat.name_parts('this IS a sillyNAME')
        ['this', 'IS', 'a', 'silly', 'N', 'A', 'M', 'E']
        >>> FileFormat.name_parts('tHis is A Silly naME')
        ['t', 'His', 'is', 'A', 'Silly', 'na', 'M', 'E']
        """
        # str(name) converts name to string in case it is a py2k
        # unicode string
        name = str(name)
        # separate at symbols
        parts = cls._RE_NAME_SEP.split(name)
        # seperate digits
        newparts = []
        for part in parts:
            for part_groups in cls._RE_NAME_DIGITS.findall(part):
                for group in part_groups:
                    if group:
                        newparts.append(group)
                        break
        parts = newparts
        # separate at upper case characters for CamelCase and camelCase words
        newparts = []
        for part in parts:
            if cls._RE_NAME_LC.search(part) and cls._RE_NAME_UC.search(part):
                # find the camel bumps
                for part_groups in cls._RE_NAME_CAMEL.findall(part):
                    for group in part_groups:
                        if group:
                            newparts.append(group)
                            break
            else:
                newparts.append(part)
        parts = newparts
        # return result
        return parts

    @classmethod
    def name_attribute(cls, name):
        """Converts an attribute name, as in the description file,
        into a name usable by python.

        :param name: The attribute name.
        :type name: ``str``
        :return: Reformatted attribute name, useable by python.

        >>> FileFormat.name_attribute('tHis is A Silly naME')
        't_his_is_a_silly_na_m_e'
        >>> FileFormat.name_attribute('Test:Something')
        'test_something'
        >>> FileFormat.name_attribute('unknown?')
        'unknown'
        """
        return '_'.join(part.lower() for part in cls.name_parts(name))

    @classmethod
    def name_class(cls, name):
        """Converts a class name, as in the xsd file, into a name usable
        by python.

        :param name: The class name.
        :type name: str
        :return: Reformatted class name, useable by python.

        >>> FileFormat.name_class('this IS a sillyNAME')
        'ThisIsASillyNAME'
        """
        return ''.join(part.capitalize()
                       for part in cls.name_parts(name))

    @classmethod
    def walkData(cls, top, topdown=True, mode='rb'):
        """A generator which yields the data of all files in
        directory top whose filename matches the regular expression
        :attr:`RE_FILENAME`. The argument top can also be a file instead of a
        directory. Errors coming from os.walk are ignored.

        Note that the caller is not responsible for closing the stream.

        This function is for instance used by :mod:`pyffi.spells` to implement
        modifying a file after reading and parsing.

        :param top: The top folder.
        :type top: ``str``
        :param topdown: Determines whether subdirectories should be iterated
            over first.
        :type topdown: ``bool``
        :param mode: The mode in which to open files.
        :type mode: ``str``
        """
        # now walk over all these files in directory top
        for filename in pyffi.utils.walk(top, topdown, onerror=None,
                                         re_filename=cls.RE_FILENAME):
            stream = open(filename, mode)
            try:
                # return data for the stream
                # the caller can call data.read(stream),
                # or data.inspect(stream), etc.
                yield stream, cls.Data()
            finally:
                stream.close()

    @classmethod
    def walk(cls, top, topdown=True, mode='rb'):
        """A generator which yields all files in
        directory top whose filename matches the regular expression
        :attr:`RE_FILENAME`. The argument top can also be a file instead of a
        directory. Errors coming from os.walk are ignored.

        Note that the caller is not responsible for closing the stream.

        This function is for instance used by :mod:`pyffi.spells` to implement
        modifying a file after reading and parsing.

        :param top: The top folder.
        :type top: ``str``
        :param topdown: Determines whether subdirectories should be iterated
            over first.
        :type topdown: ``bool``
        :param mode: The mode in which to open files.
        :type mode: ``str``
        """
        # now walk over all these files in directory top
        for filename in pyffi.utils.walk(top, topdown, onerror=None,
                                         re_filename=cls.RE_FILENAME):
            stream = open(filename, mode)
            try:
                yield stream
            finally:
                stream.close()

class ArchiveFileFormat(FileFormat):
    """This class is the base class for all archive file formats. It
    implements incremental reading and writing of archive files.
    """

    class Data(FileFormat.Data):
        """Base class for representing archive data.
        Override this class to implement incremental reading and writing.
        """

        _stream = None
        """The file stream associated with the archive."""

        def __init__(self, name=None, mode=None, fileobj=None):
            """Sets _stream and _mode."""
            # at least:
            #self._stream = fileobj if fileobj else open(name, mode)
            raise NotImplementedError

        def get_members(self):
            raise NotImplementedError

        def set_members(self, members):
            raise NotImplementedError

        def close(self):
            # at least:
            #self._stream.close()
            raise NotImplementedError

        def read(self, stream):
            self.__init__(mode='r', stream=stream)

        def write(self, stream):
            if self._stream == stream:
                raise ValueError("cannot write back to the same stream")
            # get all members from the old stream
            members = list(self.get_members())
            self.__init__(mode='w', fileobj=stream)
            # set all members to the new stream
            self.set_members(members)

class ArchiveMember(object):
    stream = None
    """Temporary file stream which contains the extracted data."""

    name = None
    """Name of the file as recorded in the archive."""
