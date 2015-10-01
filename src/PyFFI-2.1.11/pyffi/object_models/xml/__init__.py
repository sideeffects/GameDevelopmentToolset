"""Format classes and metaclasses for binary file formats described by an xml
file, and xml handler for converting the xml description into Python classes.
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

import logging
import time # for timing stuff
import types
import os.path
import sys
import xml.sax

import pyffi.object_models
from pyffi.object_models.xml.struct_    import StructBase
from pyffi.object_models.xml.basic      import BasicBase
from pyffi.object_models.xml.bit_struct import BitStructBase
from pyffi.object_models.xml.enum       import EnumBase
from pyffi.object_models.xml.expression import Expression


class MetaFileFormat(pyffi.object_models.MetaFileFormat):
    """The MetaFileFormat metaclass transforms the XML description
    of a file format into a bunch of classes which can be directly
    used to manipulate files in this format.

    The actual implementation of the parser is delegated to
    pyffi.object_models.xml.FileFormat.
    """

    def __init__(cls, name, bases, dct):
        """This function constitutes the core of the class generation
        process. For instance, we declare NifFormat to have metaclass
        MetaFileFormat, so upon creation of the NifFormat class,
        the __init__ function is called, with

        :param cls: The class created using MetaFileFormat, for example
            NifFormat.
        :param name: The name of the class, for example 'NifFormat'.
        :param bases: The base classes, usually (object,).
        :param dct: A dictionary of class attributes, such as 'xml_file_name'.
        """

        super(MetaFileFormat, cls).__init__(name, bases, dct)

        # preparation: make deep copy of lists of enums, structs, etc.
        cls.xml_enum = cls.xml_enum[:]
        cls.xml_alias = cls.xml_alias[:]
        cls.xml_bit_struct = cls.xml_bit_struct[:]
        cls.xml_struct = cls.xml_struct[:]

        # parse XML

        # we check dct to avoid parsing the same file more than once in
        # the hierarchy
        xml_file_name = dct.get('xml_file_name')
        if xml_file_name:
            # set up XML parser
            parser = xml.sax.make_parser()
            parser.setContentHandler(XmlSaxHandler(cls, name, bases, dct))

            # open XML file
            xml_file = cls.openfile(xml_file_name, cls.xml_file_path)

            # parse the XML file: control is now passed on to XmlSaxHandler
            # which takes care of the class creation
            cls.logger.debug("Parsing %s and generating classes."
                             % xml_file_name)
            start = time.clock()
            try:
                parser.parse(xml_file)
            finally:
                xml_file.close()
            cls.logger.debug("Parsing finished in %.3f seconds."
                             % (time.clock() - start))


class FileFormat(pyffi.object_models.FileFormat):
    """This class can be used as a base class for file formats
    described by an xml file."""
    __metaclass__ = MetaFileFormat
    xml_file_name = None #: Override.
    xml_file_path = None #: Override.
    logger = logging.getLogger("pyffi.object_models.xml")

    # We also keep an ordered list of all classes that have been created.
    # The xml_struct list includes all xml generated struct classes,
    # including those that are replaced by a native class in cls (for
    # instance NifFormat.String). The idea is that these lists should
    # contain sufficient info from the xml so they can be used to write
    # other python scripts that would otherwise have to implement their own
    # xml parser. See makehsl.py for an example of usage.
    #
    # (note: no classes are created for basic types, so no list for those)
    xml_enum = []
    xml_alias = []
    xml_bit_struct = []
    xml_struct = []

    @classmethod
    def vercondFilter(cls, expression):
        raise NotImplementedError


class StructAttribute(object):
    """Helper class to collect attribute data of struct add tags."""

    name = None
    """The name of this member variable."""

    type_ = None
    """The type of this member variable (type is ``str`` for forward
    declarations, and resolved to :class:`BasicBase` or
    :class:`StructBase` later).
    """

    default = None
    """The default value of this member variable."""

    template = None
    """The template type of this member variable (initially ``str``,
    resolved to :class:`BasicBase` or :class:`StructBase` at the end
    of the xml parsing), and if there is no template type, then this
    variable will equal ``type(None)``.
    """

    arg = None
    """The argument of this member variable."""

    arr1 = None
    """The first array size of this member variable, as
    :class:`Expression` or ``type(None)``.
    """

    arr2 = None
    """The second array size of this member variable, as
    :class:`Expression` or ``type(None)``.
    """

    cond = None
    """The condition of this member variable, as
    :class:`Expression` or ``type(None)``.
    """

    ver1 = None
    """The first version this member exists, as ``int``, and ``None`` if
    there is no lower limit.
    """

    ver2 = None
    """The last version this member exists, as ``int``, and ``None`` if
    there is no upper limit.
    """

    userver = None
    """The user version this member exists, as ``int``, and ``None`` if
    it exists for all user versions.
    """

    is_abstract = False
    """Whether the attribute is abstract or not (read and written)."""

    def __init__(self, cls, attrs):
        """Initialize attribute from the xml attrs dictionary of an
        add tag.

        :param cls: The class where all types reside.
        :param attrs: The xml add tag attribute dictionary."""
        # mandatory parameters
        self.displayname = attrs["name"]
        self.name = cls.name_attribute(self.displayname)
        try:
            attrs_type_str = attrs["type"]
        except KeyError:
            raise AttributeError("'%s' is missing a type attribute"
                                 % self.displayname)
        if attrs_type_str != "TEMPLATE":
            try:
                self.type_ = getattr(cls, attrs_type_str)
            except AttributeError:
                # forward declaration, resolved at endDocument
                self.type_ = attrs_type_str
        else:
            self.type_ = type(None) # type determined at runtime
        # optional parameters
        self.default = attrs.get("default")
        self.template = attrs.get("template") # resolved in endDocument
        self.arg = attrs.get("arg")
        self.arr1 = attrs.get("arr1")
        self.arr2 = attrs.get("arr2")
        self.cond = attrs.get("cond")
        self.vercond = attrs.get("vercond")
        self.ver1 = attrs.get("ver1")
        self.ver2 = attrs.get("ver2")
        self.userver = attrs.get("userver")
        self.doc = "" # handled in xml parser's characters function
        self.is_abstract = (attrs.get("abstract") == "1")

        # post-processing
        if self.default:
            try:
                tmp = self.type_()
                tmp.set_value(self.default)
                self.default = tmp.get_value()
                del tmp
            except Exception:
                # conversion failed; not a big problem
                self.default = None
        if self.arr1:
            self.arr1 = Expression(self.arr1, cls.name_attribute)
        if self.arr2:
            self.arr2 = Expression(self.arr2, cls.name_attribute)
        if self.cond:
            self.cond = Expression(self.cond, cls.name_attribute)
        if self.vercond:
            self.vercond = Expression(self.vercond, cls.vercondFilter)
            #print(self.vercond)
        if self.arg:
            try:
                self.arg = int(self.arg)
            except ValueError:
                self.arg = cls.name_attribute(self.arg)
        if self.userver:
            self.userver = int(self.userver)
        if self.ver1:
            self.ver1 = cls.version_number(self.ver1)
        if self.ver2:
            self.ver2 = cls.version_number(self.ver2)


class BitStructAttribute(object):
    """Helper class to collect attribute data of bitstruct bits tags."""

    def __init__(self, cls, attrs):
        """Initialize attribute from the xml attrs dictionary of an
        add tag.

        :param cls: The class where all types reside.
        :param attrs: The xml add tag attribute dictionary."""
        # mandatory parameters
        self.name = cls.name_attribute(attrs["name"])
        self.numbits = int(cls.name_attribute(attrs["numbits"]))
        # optional parameters
        self.default = attrs.get("default")
        self.cond = attrs.get("cond")
        self.ver1 = attrs.get("ver1")
        self.ver2 = attrs.get("ver2")
        self.userver = attrs.get("userver")
        self.doc = "" # handled in xml parser's characters function

        # post-processing
        if self.default:
            self.default = int(self.default)
        if self.cond:
            self.cond = Expression(self.cond, cls.name_attribute)
        if self.userver:
            self.userver = int(self.userver)
        if self.ver1:
            self.ver1 = cls.version_number(self.ver1)
        if self.ver2:
            self.ver2 = cls.version_number(self.ver2)


class XmlError(Exception):
    """The XML handler will throw this exception if something goes wrong while
    parsing."""
    pass


class XmlSaxHandler(xml.sax.handler.ContentHandler):
    """This class contains all functions for parsing the xml and converting
    the xml structure into Python classes."""
    tag_file = 1
    tag_version = 2
    tag_basic = 3
    tag_alias = 4
    tag_enum = 5
    tag_option = 6
    tag_bit_struct = 7
    tag_struct = 8
    tag_attribute = 9
    tag_bits = 10

    tags = {
    "fileformat": tag_file,
    "version": tag_version,
    "basic": tag_basic,
    "alias": tag_alias,
    "enum": tag_enum,
    "option": tag_option,
    "bitstruct": tag_bit_struct,
    "struct": tag_struct,
    "bits": tag_bits,
    "add": tag_attribute}

    # for compatibility with niftools
    tags_niftools = {
    "niftoolsxml": tag_file,
    "compound": tag_struct,
    "niobject": tag_struct,
    "bitflags": tag_bit_struct}

    def __init__(self, cls, name, bases, dct):
        """Set up the xml parser.

        Upon instantiation this function does the following:
          - Creates a dictionary C{cls.versions} which maps each supported
            version strings onto a version integer.
          - Creates a dictionary C{cls.games} which maps each supported game
            onto a list of versions.
          - Makes an alias C{self.cls} for C{cls}.
          - Initializes a stack C{self.stack} of xml tags.
          - Initializes the current tag.
        """
        # initialize base class (no super because base class is old style)
        xml.sax.handler.ContentHandler.__init__(self)

        # save dictionary for future use
        self.dct = dct

        # initialize dictionaries
        # cls.version maps each supported version string to a version number
        cls.versions = {}
        # cls.games maps each supported game to a list of header version
        # numbers
        cls.games = {}
        # note: block versions are stored in the _games attribute of the
        # struct class

        # initialize tag stack
        self.stack = []
        # keep track last element of self.stack
        # storing this reduces overhead as profiling has shown
        self.current_tag = None

        # cls needs to be accessed in member functions, so make it an instance
        # member variable
        self.cls = cls

        # elements for creating new classes
        self.class_name = None
        self.class_dict = None
        self.class_bases = ()

        # elements for basic classes
        self.basic_class = None

        # elements for versions
        self.version_string = None

    def pushTag(self, tag):
        """Push tag C{tag} on the stack and make it the current tag.

        :param tag: The tag to put on the stack."""
        self.stack.insert(0, tag)
        self.current_tag = tag

    def popTag(self):
        """Pop the current tag from the stack and return it. Also update
        the current tag.

        :return: The tag popped from the stack."""
        lasttag = self.stack.pop(0)
        try:
            self.current_tag = self.stack[0]
        except IndexError:
            self.current_tag = None
        return lasttag

    def startElement(self, name, attrs):
        """Called when parser starts parsing an element called C{name}.

        This function sets up all variables for creating the class
        in the C{self.endElement} function. For struct elements, it will set up
        C{self.class_name}, C{self.class_bases}, and C{self.class_dict} which
        will be used to create the class by invokation of C{type} in
        C{self.endElement}. For basic, enum, and bitstruct elements, it will
        set up C{self.basic_class} to link to the proper class implemented by
        C{self.cls}. The code also performs sanity checks on the attributes.

        For xml add tags, the function will add an entry to the
        C{self.class_dict["_attrs"]} list. Note that this list is used by the
        struct metaclass: the class attributes are created exactly from this
        list.

        :param name: The name of the xml element.
        :param attrs: A dictionary of attributes of the element."""
        # get the tag identifier
        try:
            tag = self.tags[name]
        except KeyError:
            try:
                tag = self.tags_niftools[name]
            except KeyError:
                raise XmlError("error unknown element '%s'" % name)

        # Check the stack, if the stack does not exist then we must be
        # at the root of the xml file, and the tag must be "fileformat".
        # The fileformat tag has no further attributes of interest,
        # so we can exit the function after pushing the tag on the stack.
        if not self.stack:
            if tag != self.tag_file:
                raise XmlError("this is not a fileformat xml file")
            self.pushTag(tag)
            return

        # Now do a number of things, depending on the tag that was last
        # pushed on the stack; this is self.current_tag, and reflects the
        # tag in which <name> is embedded.
        #
        # For each struct, alias, enum, and bitstruct tag, we shall
        # create a class. So assign to C{self.class_name} the name of that
        # class, C{self.class_bases} to the base of that class, and
        # C{self.class_dict} to the class dictionary.
        #
        # For a basic tag, C{self.class_name} is the name of the
        # class and C{self.basic_class} is the corresponding class in
        # C{self.cls}.
        #
        # For a version tag, C{self.version_string} describes the version as a
        # string.
        if self.current_tag == self.tag_struct:
            self.pushTag(tag)
            # struct -> attribute
            if tag == self.tag_attribute:
                # add attribute to class dictionary
                self.class_dict["_attrs"].append(
                    StructAttribute(self.cls, attrs))
            # struct -> version
            elif tag == self.tag_version:
                # set the version string
                self.version_string = str(attrs["num"])
                self.cls.versions[self.version_string] = self.cls.version_number(
                    self.version_string)
                # (class_dict["_games"] is updated when reading the characters)
            else:
                raise XmlError(
                    "only add and version tags allowed in struct declaration")
        elif self.current_tag == self.tag_file:
            self.pushTag(tag)

            # fileformat -> struct
            if tag == self.tag_struct:
                self.class_name = attrs["name"]
                # struct types can be organized in a hierarchy
                # if inherit attribute is defined, then look for corresponding
                # base block
                class_basename = attrs.get("inherit")
                if class_basename:
                    # if that base struct has not yet been assigned to a
                    # class, then we have a problem
                    try:
                        self.class_bases += (
                            getattr(self.cls, class_basename), )
                    except KeyError:
                        raise XmlError(
                            "typo, or forward declaration of struct %s"
                            % class_basename)
                else:
                    self.class_bases = (StructBase,)
                # istemplate attribute is optional
                # if not set, then the struct is not a template
                # set attributes (see class StructBase)
                self.class_dict = {
                    "_is_template": attrs.get("istemplate") == "1",
                    "_attrs": [],
                    "_games": {},
                    "__doc__": "",
                    "__module__": self.cls.__module__}

            # fileformat -> basic
            elif tag == self.tag_basic:
                self.class_name = attrs["name"]
                # Each basic type corresponds to a type defined in C{self.cls}.
                # The link between basic types and C{self.cls} types is done
                # via the name of the class.
                self.basic_class = getattr(self.cls, self.class_name)
                # check the class variables
                is_template = (attrs.get("istemplate") == "1")
                if self.basic_class._is_template != is_template:
                    raise XmlError(
                        'class %s should have _is_template = %s'
                        % (self.class_name, is_template))

            # fileformat -> enum
            elif tag == self.tag_enum:
                self.class_bases += (EnumBase,)
                self.class_name = attrs["name"]
                try:
                    numbytes = int(attrs["numbytes"])
                except KeyError:
                    # niftools format uses a storage
                    # get number of bytes from that
                    typename = attrs["storage"]
                    try:
                        typ = getattr(self.cls, typename)
                    except AttributeError:
                        raise XmlError(
                            "typo, or forward declaration of type %s"
                            % typename)
                    numbytes = typ.get_size()
                self.class_dict = {"__doc__": "",
                                  "_numbytes": numbytes,
                                  "_enumkeys": [], "_enumvalues": [],
                                  "__module__": self.cls.__module__}

            # fileformat -> alias
            elif tag == self.tag_alias:
                self.class_name = attrs["name"]
                typename = attrs["type"]
                try:
                    self.class_bases += (getattr(self.cls, typename),)
                except AttributeError:
                    raise XmlError(
                        "typo, or forward declaration of type %s" % typename)
                self.class_dict = {"__doc__": "",
                                  "__module__": self.cls.__module__}

            # fileformat -> bitstruct
            # this works like an alias for now, will add special
            # BitStruct base class later
            elif tag == self.tag_bit_struct:
                self.class_bases += (BitStructBase,)
                self.class_name = attrs["name"]
                try:
                    numbytes = int(attrs["numbytes"])
                except KeyError:
                    # niftools style: storage attribute
                    numbytes = getattr(self.cls, attrs["storage"]).get_size()
                self.class_dict = {"_attrs": [], "__doc__": "",
                                  "_numbytes": numbytes,
                                  "__module__": self.cls.__module__}

            # fileformat -> version
            elif tag == self.tag_version:
                self.version_string = str(attrs["num"])
                self.cls.versions[self.version_string] = self.cls.version_number(
                    self.version_string)
                # (self.cls.games is updated when reading the characters)

            else:
                raise XmlError("""
expected basic, alias, enum, bitstruct, struct, or version,
but got %s instead""" % name)

        elif self.current_tag == self.tag_version:
            raise XmlError("version tag must not contain any sub tags")

        elif self.current_tag == self.tag_alias:
            raise XmlError("alias tag must not contain any sub tags")

        elif self.current_tag == self.tag_enum:
            self.pushTag(tag)
            if not tag == self.tag_option:
                raise XmlError("only option tags allowed in enum declaration")
            value = attrs["value"]
            try:
                # note: use long rather than int to work around 0xffffffff
                # error in qskope
                value = long(value)
            except ValueError:
                value = long(value, 16)
            self.class_dict["_enumkeys"].append(attrs["name"])
            self.class_dict["_enumvalues"].append(value)

        elif self.current_tag == self.tag_bit_struct:
            self.pushTag(tag)
            if tag == self.tag_bits:
                # mandatory parameters
                self.class_dict["_attrs"].append(
                    BitStructAttribute(self.cls, attrs))
            elif tag == self.tag_option:
                # niftools compatibility, we have a bitflags field
                # so convert value into numbits
                # first, calculate current bit position
                bitpos = sum(bitattr.numbits
                             for bitattr in self.class_dict["_attrs"])
                # check if extra bits must be inserted
                numextrabits = int(attrs["value"]) - bitpos
                if numextrabits < 0:
                    raise XmlError("values of bitflags must be increasing")
                if numextrabits > 0:
                    self.class_dict["_attrs"].append(
                        BitStructAttribute(
                            self.cls,
                            dict(name="Reserved Bits %i"
                                 % len(self.class_dict["_attrs"]),
                                 numbits=numextrabits)))
                # add the actual attribute
                self.class_dict["_attrs"].append(
                    BitStructAttribute(
                        self.cls,
                        dict(name=attrs["name"], numbits=1)))
            else:
                raise XmlError(
                    "only bits tags allowed in struct type declaration")

        else:
            raise XmlError("unhandled tag %s" % name)

    def endElement(self, name):
        """Called at the end of each xml tag.

        Creates classes."""
        if not self.stack:
            raise XmlError("mismatching end element tag for element %s" % name)
        try:
            tag = self.tags[name]
        except KeyError:
            try:
                tag = self.tags_niftools[name]
            except KeyError:
                raise XmlError("error unknown element %s" % name)
        if self.popTag() != tag:
            raise XmlError("mismatching end element tag for element %s" % name)
        elif tag == self.tag_attribute:
            return # improves performance
        elif tag in (self.tag_struct,
                     self.tag_enum,
                     self.tag_alias,
                     self.tag_bit_struct):
            # create class
            # assign it to cls.<class_name> if it has not been implemented
            # internally
            cls_klass = getattr(self.cls, self.class_name, None)
            if cls_klass and issubclass(cls_klass, BasicBase):
                # overrides a basic type - not much to do
                pass
            else:
                # check if we have a customizer class
                if cls_klass:
                    # exists: create and add to base class of customizer
                    gen_klass = type(
                        "_" + str(self.class_name),
                        self.class_bases, self.class_dict)
                    setattr(self.cls, "_" + self.class_name, gen_klass)
                    # recreate the class, to ensure that the
                    # metaclass is called!!
                    # (otherwise, cls_klass does not have correct
                    # _attribute_list, etc.)
                    cls_klass = type(
                        cls_klass.__name__,
                        (gen_klass,) + cls_klass.__bases__,
                        dict(cls_klass.__dict__))
                    setattr(self.cls, self.class_name, cls_klass)
                    # if the class derives from Data, then make an alias
                    if issubclass(
                        cls_klass,
                        pyffi.object_models.FileFormat.Data):
                        self.cls.Data = cls_klass
                    # for the stuff below
                    gen_class = cls_klass
                else:
                    # does not yet exist: create it and assign to class dict
                    gen_klass = type(
                        str(self.class_name), self.class_bases, self.class_dict)
                    setattr(self.cls, self.class_name, gen_klass)
                # append class to the appropriate list
                if tag == self.tag_struct:
                    self.cls.xml_struct.append(gen_klass)
                elif tag == self.tag_enum:
                    self.cls.xml_enum.append(gen_klass)
                elif tag == self.tag_alias:
                    self.cls.xml_alias.append(gen_klass)
                elif tag == self.tag_bit_struct:
                    self.cls.xml_bit_struct.append(gen_klass)
            # reset variables
            self.class_name = None
            self.class_dict = None
            self.class_bases = ()
        elif tag == self.tag_basic:
            # link class cls.<class_name> to self.basic_class
            setattr(self.cls, self.class_name, self.basic_class)
            # reset variable
            self.basic_class = None
        elif tag == self.tag_version:
            # reset variable
            self.version_string = None

    def endDocument(self):
        """Called when the xml is completely parsed.

        Searches and adds class customized functions.
        For version tags, adds version to version and game lists."""
        for obj in self.cls.__dict__.values():
            # skip objects that are not generated by the C{type} function
            # or that do not derive from StructBase
            if not (isinstance(obj, type) and issubclass(obj, StructBase)):
                continue
            # fix templates
            for attr in obj._attrs:
                templ = attr.template
                if isinstance(templ, basestring):
                    attr.template = \
                        getattr(self.cls, templ) if templ != "TEMPLATE" \
                        else type(None)
                attrtype = attr.type_
                if isinstance(attrtype, basestring):
                    attr.type_ = getattr(self.cls, attrtype)

    def characters(self, chars):
        """Add the string C{chars} to the docstring.
        For version tags, updates the game version list."""
        if self.current_tag in (self.tag_attribute, self.tag_bits):
            self.class_dict["_attrs"][-1].doc += str(chars.strip())
        elif self.current_tag in (self.tag_struct, self.tag_enum,
                                 self.tag_alias):
            self.class_dict["__doc__"] += str(chars.strip())
        elif self.current_tag == self.tag_version:
            # fileformat -> version
            if self.stack[1] == self.tag_file:
                gamesdict = self.cls.games
            # struct -> version
            elif self.stack[1] == self.tag_struct:
                gamesdict = self.class_dict["_games"]
            else:
                raise XmlError("version parsing error at '%s'" % chars)
            # update the gamesdict dictionary
            for gamestr in (str(g.strip()) for g in chars.split(',')):
                if gamestr in gamesdict:
                    gamesdict[gamestr].append(
                        self.cls.versions[self.version_string])
                else:
                    gamesdict[gamestr] = [
                        self.cls.versions[self.version_string]]
