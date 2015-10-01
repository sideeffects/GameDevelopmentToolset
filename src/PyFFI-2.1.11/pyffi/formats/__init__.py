"""
:mod:`pyffi.formats` --- File format interfaces
===============================================

When experimenting with any of the supported file formats, you can specify
an alternate location where you store your modified format description by means
of an environment variable. For instance,
to tell the library to use your version of :file:`cgf.xml`,
set the :envvar:`CGFXMLPATH` environment variable to the directory where
:file:`cgf.xml` can be found. The environment variables :envvar:`NIFXMLPATH`,
:envvar:`KFMXMLPATH`, :envvar:`DDSXMLPATH`, and :envvar:`TGAXMLPATH`
work similarly.

Supported formats
-----------------

.. toctree::
   :maxdepth: 2

   pyffi.formats.bsa
   pyffi.formats.cgf
   pyffi.formats.dae
   pyffi.formats.dds
   pyffi.formats.egm
   pyffi.formats.egt
   pyffi.formats.esp
   pyffi.formats.kfm
   pyffi.formats.nif
   pyffi.formats.tga
   pyffi.formats.tri

Adding new formats
------------------

This section tries to explain how you can implement your own format in pyffi.

Getting Started
^^^^^^^^^^^^^^^

Note that the files which make up the following example can all be found in
the examples/simple directory of the source distribution of pyffi.

Suppose you have a simple file format, which consists of an integer,
followed by a list of integers as many as described by the first
integer. We start by creating an XML file, call it :file:`simple.xml`,
which describes this format in a way that pyffi can understand:

.. literalinclude:: ../examples/simple/simple.xml
    :language: xml

What pyffi does is convert this simple XML description into Python classes
which automatically can read and write the structure you've just described.
Say this is the contents of :file:`simple.py`:

.. literalinclude:: ../examples/simple/simple.py
    :language: python

What happens in this piece of code?

  - The :class:`pyffi.object_models.xml.FileFormat`
    base class triggers the transformation of xml into Python classes;
    how these classes can be used will be explained further.

  - The :attr:`~pyffi.object_models.xml.FileFormat.xml_file_name`
    class attribute provides the name of the xml file that describes
    the structures we wish to generate. The
    :attr:`~pyffi.object_models.xml.FileFormat.xml_file_path`
    attribute gives a list of locations of where to look for this
    file; in our case we have simply chosen to put :file:`simple.xml`
    in the same directory as :file:`simple.py`.

  - The :class:`SimpleFormat.Example` class
    provides the generated class with a function :meth:`addInteger` in
    addition to the attributes :attr:`numIntegers` and
    :attr:`integers` which have been created from the XML.

  - Finally, the :mod:`pyffi.object_models.common` module implements
    the most common basic types, such as integers, characters, and
    floats. In the above example we have taken advantage of
    :class:`pyffi.object_models.common.Int`, which defines a signed
    32-bit integer, exactly the type we need.

Reading and Writing Files
^^^^^^^^^^^^^^^^^^^^^^^^^

To read the contents of a file of the format described by
simple.xml:

.. literalinclude:: ../examples/simple/testread.py
    :language: python

Or, to create a new file in this format:

.. literalinclude:: ../examples/simple/testwrite.py
    :language: python

Further References
^^^^^^^^^^^^^^^^^^

With the above simple example in mind, you may wish to browse through
the source code of :mod:`pyffi.formats.cgf` or
:mod:`pyffi.formats.nif` to see how pyffi works for more complex file
formats.
"""
