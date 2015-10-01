"""This script simply serves as a conceptual example on how classes could
be created from an xml file. For simplicity, no actual xml file is involved
and the class data (attribute names and their default values) is described
in a dictionary.

The MetaFileFormat class does all the hard work in converting the
dictionary data into real classes. The _Block class is a helper class for
describing an arbitrary structure. _MetaBlock simply checks a _Block class
for the presence of particular attributes.
"""

DEBUG = False

# This metaclass checks for the presence of an _attrs and __doc__ attribute.
# Used as metaclass of _Block.
class _MetaBlock(type):
    def __init__(cls, name, bases, dct):
        # consistency checks
        if not dct.has_key('_attrs'):
            raise TypeError(str(cls) + ': missing _attrs attribute')
        if not dct.has_key('__doc__'):
            raise TypeError(str(cls) + ': missing __doc__ attribute')

class _Block(object):
    """Base class from which all file block types are derived.

    The _Block class implements the basic block interface:
    it will initialize all attributes using the class interface
    using the _attrs class variable, print them as strings, and so on.
    The class variable _attrs *must* be declared every derived class
    interface, see MetaFileFormat.__init__ for an example.
    """
    __metaclass__ = _MetaBlock
    _attrs = ()
    # initialize all _attrs attributes
    def __init__(self):
        self._initAttributes(self.__class__)

    # initialize all attributes in cls._attrs
    # (plus all bases of cls)
    def _initAttributes(self, cls):
        # are we at the end of class recursion?
        if cls == object: return
        # initialize attributes of base classes of cls
        for base in cls.__bases__:
            self._initAttributes(base)
        # initialize attributes defined in cls._attrs
        for name, default in cls._attrs:
            setattr(self, name, default)

    # string representation of all _attrs attributes
    def __str__(self):
        return self._strAttributes(self.__class__)

    # string of all attributes in cls._attrs
    # (plus all bases of cls)
    def _strAttributes(self, cls):
        s = ''
        # are we at the end of class recursion?
        if cls == object: return s
        # string of attributes of base classes of cls
        for base in cls.__bases__:
            s += self._strAttributes(base)
        # string of attributes defined in cls._attrs
        for name, default in cls._attrs:
            s += str(name) + ' : ' + str(getattr(self, name)) + '\n'
        return s

# The MetaFileFormat class transforms the XML description of a file format
# into a bunch of classes via the "type(name, bases, dct)" factory.
# Because its base is type, MetaFileFormat is a metaclass: each file format
# corresponds to a separate class with subclasses corresponding to different
# file block types, compound types, enum types, and basic types.
class MetaFileFormat(type):
    # The following function constitutes the core of the class generation
    # process. Below, we declare NifFormat to have metaclass MetaFileFormat,
    # so upon creation of the NifFormat class, the __init__ function is
    # called, with
    #
    #   cls   : NifFormat
    #   name  : "NifFormat"
    #   bases : a tuple (object,) since NifFormat is derived from object
    #   dct   : a dictionary describing all attributes of the NifFormat
    #           class, such as 'xml_file_name'
    #           (in other words, any attribute defined in the class interface
    #           is accessible through dct)
    def __init__(cls, name, bases, dct):
        # of course we should read the data from file dct['xml_file_name']
        # the code below is only a proof of concept
        block_name = 'NiObjectNET'
        block_ancestor = _Block # base of all block classes
        block_dct = {}
        # add docstring
        block_dct['__doc__'] = 'Some nif object.'
        # add class variable <block_name>._attrs, which
        # is a tuple containing all attributes: their name, default, and so on
        # (to be extended! probably have a tuple of Attribute instances
        # instead of a tuple of tuples)
        block_dct['_attrs'] = ( ('name', 'noname'), )
        # create class cls.<block_name>
        setattr(cls, block_name, type(block_name, (block_ancestor,), block_dct))
        if DEBUG: print 'cls.NiObjectNET: ', dir(cls.NiObjectNET) # debug

        # do another one
        block_name = 'NiNode'
        block_ancestor = getattr(cls, 'NiObjectNET')
        block_dct = {}
        block_dct['__doc__'] = 'Basic node.'
        block_dct['_attrs'] = ( ('translateX', 0.0), ('translateY', 0.0), ('translateZ', 0.0) )
        setattr(cls, block_name, type(block_name, (block_ancestor,), block_dct))
        if DEBUG: print 'cls.NiNode: ', dir(cls.NiNode) # debug



# The NifFormat class simply processes nif.xml via MetaFileFormat
# which generates subclasses of NifFormat for basic types, compounds,
# blocks, and enums.
class NifFormat(object):
    __metaclass__ = MetaFileFormat
    xml_file_name = "nif.xml"

# For example, NifFormat.NiNode is now a class representing the NiNode block
# type! The _Block class, from which NifFormat.NiNode is derived, takes care
# of initialization of all attributes, and printing them.

if DEBUG:
    print NifFormat
    print dir(NifFormat)
    print NifFormat.NiObjectNET
    print dir(NifFormat.NiObjectNET)
    print NifFormat.NiNode
    print dir(NifFormat.NiNode)

# as a test, let's create a few blocks, fill them with data, and print them
blk0 = NifFormat.NiObjectNET()
blk1 = NifFormat.NiNode()
blk2 = NifFormat.NiNode()

blk0.name = 'hello'
blk1.name = 'world'
blk1.translateX = 1.2
blk2.name = 'awesome!'
blk2.translateY = 3.4

print blk0
print blk1
print blk2
