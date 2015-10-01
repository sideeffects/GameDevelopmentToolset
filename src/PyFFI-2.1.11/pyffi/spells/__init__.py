"""
:mod:`pyffi.spells` --- High level file operations
==================================================

.. note::
   
   This module is based on wz's NifTester module, although
   nothing of wz's original code is left in this module.

A :term:`toaster`, implemented by subclasses of the abstract
:class:`Toaster` class, walks over all files in a folder, and applies
one or more transformations on each file. Such transformations are
called :term:`spell`\ s, and are implemented by subclasses of the
abstract :class:`Spell` class.

A :term:`spell` can also run independently of a :term:`toaster` and be
applied on a branch directly. The recommended way of doing this is via
the :meth:`Spell.recurse` method.

Supported spells
----------------

For format specific spells, refer to the corresponding module.

.. toctree::
   :maxdepth: 2
   
   pyffi.spells.cgf
   pyffi.spells.dae
   pyffi.spells.dds
   pyffi.spells.kfm
   pyffi.spells.nif
   pyffi.spells.tga

Some spells are applicable on every file format, and those are documented
here.

.. autoclass:: SpellApplyPatch
   :show-inheritance:
   :members:

Adding new spells
-----------------

To create new spells, derive your custom spells from the :class:`Spell`
class, and include them in the :attr:`Toaster.SPELLS` attribute of your
toaster.

.. autoclass:: Spell
   :show-inheritance:
   :members: READONLY, SPELLNAME, data, stream, toaster,
             __init__, recurse, _datainspect, datainspect, _branchinspect,
             branchinspect, dataentry, dataexit, branchentry,
             branchexit, toastentry, toastexit

Grouping spells together
------------------------

It is also possible to create composite spells, that is, spells that
simply execute other spells. The following functions and classes can
be used for this purpose.

.. autofunction:: SpellGroupParallel

.. autofunction:: SpellGroupSeries

.. autoclass:: SpellGroupBase
   :show-inheritance:
   :members:
   :undoc-members:
   

.. autoclass:: SpellGroupParallelBase
   :show-inheritance:
   :members:
   :undoc-members:
   

.. autoclass:: SpellGroupSeriesBase
   :show-inheritance:
   :members:
   :undoc-members:

Creating toaster scripts
------------------------

To create a new toaster script, derive your toaster from the :class:`Toaster`
class, and set the :attr:`Toaster.FILEFORMAT` attribute of your toaster to
the file format class of the files it can toast.

.. autoclass:: Toaster
   :show-inheritance:
   :members:
   :inherited-members:
   :undoc-members:

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

from ConfigParser import ConfigParser
from copy import deepcopy
from cStringIO import StringIO
import gc
from itertools import izip
import logging # Logger
try:
    import multiprocessing # Pool
except ImportError:
    # < py26
    multiprocessing = None
import optparse
import os # remove
import os.path # getsize, split, join
import re # for regex parsing (--skip, --only)
import shlex # shlex.split for parsing option lists in ini files
import subprocess
import sys # sys.stdout
import tempfile

import pyffi # for pyffi.__version__
import pyffi.object_models # pyffi.object_models.FileFormat

class Spell(object):
    """Spell base class. A spell takes a data file and then does something
    useful with it. The main entry point for spells is :meth:`recurse`, so if you
    are writing new spells, start with reading the documentation with
    :meth:`recurse`.
    """

    data = None
    """The :class:`~pyffi.object_models.FileFormat.Data` instance
    this spell acts on."""

    stream = None
    """The current ``file`` being processed."""

    toaster = None
    """The :class:`Toaster` instance this spell is called from."""

    changed = False
    """Whether the spell changed the data. If ``True``, the file will be
    written back, otherwise not.
    """

    reports = None
    """Any information the spell wants to report back to the toaster
    (used for instance for regression testing).
    """

    # spells are readonly by default
    READONLY = True
    """A ``bool`` which determines whether the spell is read only or
    not. Default value is ``True``. Override this class attribute, and
    set to ``False``, when subclassing a spell that must write files
    back to the disk.
    """

    SPELLNAME = None
    """A ``str`` describing how to refer to the spell from the command line.
    Override this class attribute when subclassing.
    """

    def __init__(self, toaster=None, data=None, stream=None):
        """Initialize the spell data.

        :param data: The file :attr:`data`.
        :type data: :class:`~pyffi.object_models.FileFormat.Data`
        :param stream: The file :attr:`stream`.
        :type stream: ``file``
        :param toaster: The :attr:`toaster` this spell is called from (optional).
        :type toaster: :class:`Toaster`
        """
        self.data = data
        self.stream = stream
        self.toaster = toaster if toaster else Toaster()

    def _datainspect(self):
        """This is called after :meth:`pyffi.object_models.FileFormat.Data.inspect` has
        been called, and before :meth:`pyffi.object_models.FileFormat.Data.read` is
        called.

        :return: ``True`` if the file must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        # for the moment, this does nothing
        return True

    def datainspect(self):
        """This is called after :meth:`pyffi.object_models.FileFormat.Data.inspect` has
        been called, and before :meth:`pyffi.object_models.FileFormat.Data.read` is
        called. Override this function for customization.

        :return: ``True`` if the file must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        # for nif: check if version applies, or
        # check if spell block type is found
        return True

    def _branchinspect(self, branch):
        """Check if spell should be cast on this branch or not, based on
        exclude and include options passed on the command line. You should
        not need to override this function: if you need additional checks on
        whether a branch must be parsed or not, override the :meth:`branchinspect`
        method.

        :param branch: The branch to check.
        :type branch: :class:`~pyffi.utils.graph.GlobalNode`
        :return: ``True`` if the branch must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        # fall back on the toaster implementation
        return self.toaster.is_admissible_branch_class(branch.__class__)

    def branchinspect(self, branch):
        """Like :meth:`_branchinspect`, but for customization: can be overridden to
        perform an extra inspection (the default implementation always
        returns ``True``).

        :param branch: The branch to check.
        :type branch: :class:`~pyffi.utils.graph.GlobalNode`
        :return: ``True`` if the branch must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        return True

    def recurse(self, branch=None):
        """Helper function which calls :meth:`_branchinspect` and :meth:`branchinspect`
        on the branch,
        if both successful then :meth:`branchentry` on the branch, and if this is
        succesful it calls :meth:`recurse` on the branch's children, and
        once all children are done, it calls :meth:`branchexit`.

        Note that :meth:`_branchinspect` and :meth:`branchinspect` are not called upon
        first entry of this function, that is, when called with :attr:`data` as
        branch argument. Use :meth:`datainspect` to stop recursion into this branch.

        Do not override this function.

        :param branch: The branch to start the recursion from, or ``None``
            to recurse the whole tree.
        :type branch: :class:`~pyffi.utils.graph.GlobalNode`
        """
        # when called without arguments, recurse over the whole tree
        if branch is None:
            branch = self.data
        # the root data element: datainspect has already been called
        if branch is self.data:
            self.toaster.msgblockbegin(
                "--- %s ---" % self.SPELLNAME)
            if self.dataentry():
                # spell returned True so recurse to children
                # we use the abstract tree functions to parse the tree
                # these are format independent!
                for child in branch.get_global_child_nodes():
                    self.recurse(child)
                self.dataexit()
            self.toaster.msgblockend()
        elif self._branchinspect(branch) and self.branchinspect(branch):
            self.toaster.msgblockbegin(
                """~~~ %s [%s] ~~~"""
                % (branch.__class__.__name__,
                   branch.get_global_display()))
            # cast the spell on the branch
            if self.branchentry(branch):
                # spell returned True so recurse to children
                # we use the abstract tree functions to parse the tree
                # these are format independent!
                for child in branch.get_global_child_nodes():
                    self.recurse(child)
                self.branchexit(branch)
            self.toaster.msgblockend()

    def dataentry(self):
        """Called before all blocks are recursed.
        The default implementation simply returns ``True``.
        You can access the data via :attr:`data`, and unlike in the
        :meth:`datainspect` method, the full file has been processed at this stage.

        Typically, you will override this function to perform a global
        operation on the file data.

        :return: ``True`` if the children must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        return True

    def branchentry(self, branch):
        """Cast the spell on the given branch. First called with branch equal to
        :attr:`data`'s children, then the grandchildren, and so on.
        The default implementation simply returns ``True``.

        Typically, you will override this function to perform an operation
        on a particular block type and/or to stop recursion at particular
        block types.

        :param branch: The branch to cast the spell on.
        :type branch: :class:`~pyffi.utils.graph.GlobalNode`
        :return: ``True`` if the children must be processed, ``False`` otherwise.
        :rtype: ``bool``
        """
        return True

    def branchexit(self, branch):
        """Cast a spell on the given branch, after all its children,
        grandchildren, have been processed, if :meth:`branchentry` returned
        ``True`` on the given branch.

        Typically, you will override this function to perform a particular
        operation on a block type, but you rely on the fact that the children
        must have been processed first.

        :param branch: The branch to cast the spell on.
        :type branch: :class:`~pyffi.utils.graph.GlobalNode`
        """
        pass

    def dataexit(self):
        """Called after all blocks have been processed, if :meth:`dataentry`
        returned ``True``.

        Typically, you will override this function to perform a final spell
        operation, such as writing back the file in a special way, or making a
        summary log.
        """
        pass

    @classmethod
    def toastentry(cls, toaster):
        """Called just before the toaster starts processing
        all files. If it returns ``False``, then the spell is not used.
        The default implementation simply returns ``True``.

        For example, if the spell only acts on a particular block type, but
        that block type is excluded, then you can use this function to flag
        that this spell can be skipped. You can also use this function to
        initialize statistics data to be aggregated from files, to
        initialize a log file, and so.

        :param toaster: The toaster this spell is called from.
        :type toaster: :class:`Toaster`
        :return: ``True`` if the spell applies, ``False`` otherwise.
        :rtype: ``bool``
        """
        return True

    @classmethod
    def toastexit(cls, toaster):
        """Called when the toaster has finished processing
        all files.

        :param toaster: The toaster this spell is called from.
        :type toaster: :class:`Toaster`
        """
        pass

    @classmethod
    def get_toast_stream(cls, toaster, filename, test_exists=False):
        """Returns the stream that the toaster will write to. The
        default implementation calls ``toaster.get_toast_stream``, but
        spells that write to different file(s) can override this
        method.
        """
        return toaster.get_toast_stream(filename, test_exists=test_exists)

    def append_report(self, report):
        if self.reports is None:
            self.reports = []
        self.reports.append(report)

class SpellGroupBase(Spell):
    """Base class for grouping spells. This implements all the spell grouping
    functions that fall outside of the actual recursing (:meth:`__init__`,
    :meth:`toastentry`, :meth:`_datainspect`, :meth:`datainspect`, and :meth:`toastexit`).
    """

    SPELLCLASSES = []
    """List of :class:`Spell`\ s of this group (not instantiated)."""

    ACTIVESPELLCLASSES = []
    """List of active spells of this group (not instantiated).
    This list is automatically built when :meth:`toastentry` is called.
    """

    spells = []
    """List of active spell instances."""

    def __init__(self, toaster=None, data=None, stream=None):
        """Initialize the spell data for all given spells.

        :param toaster: The toaster this spell is called from.
        :type toaster: :class:`Toaster`
        :param data: The file data.
        :type data: :class:`pyffi.object_models.FileFormat.Data`
        :param stream: The file stream.
        :type stream: ``file``
        """
        # call base class constructor
        Spell.__init__(self, toaster=toaster, data=data, stream=stream)
        # set up the list of spells
        self.spells = [spellclass(toaster=toaster, data=data, stream=stream)
                       for spellclass in self.ACTIVESPELLCLASSES]

    def datainspect(self):
        """Inspect every spell with L{Spell.datainspect} and keep
        those spells that must be cast."""
        self.spells = [spell for spell in self.spells
                       if spell.datainspect()]
        return bool(self.spells)

    @classmethod
    def toastentry(cls, toaster):
        cls.ACTIVESPELLCLASSES = [
            spellclass for spellclass in cls.SPELLCLASSES
            if spellclass.toastentry(toaster)]
        return bool(cls.ACTIVESPELLCLASSES)

    @classmethod
    def toastexit(cls, toaster):
        for spellclass in cls.ACTIVESPELLCLASSES:
            spellclass.toastexit(toaster)

class SpellGroupSeriesBase(SpellGroupBase):
    """Base class for running spells in series."""
    def recurse(self, branch=None):
        """Recurse spells in series."""
        for spell in self.spells:
            spell.recurse(branch)

    # the following functions must NEVER be called in series of spells
    # everything is handled by the recurse function

    def branchinspect(self, branch):
        raise RuntimeError("use recurse")

    def branchentry(self, branch):
        raise RuntimeError("use recurse")

    def dataexit(self):
        raise RuntimeError("use recurse")

    def dataentry(self):
        raise RuntimeError("use recurse")

    def dataexit(self):
        raise RuntimeError("use recurse")

    @property
    def changed(self):
        return any(spell.changed for spell in self.spells)

class SpellGroupParallelBase(SpellGroupBase):
    """Base class for running spells in parallel (that is, with only
    a single recursion in the tree).
    """
    def branchinspect(self, branch):
        """Inspect spells with :meth:`Spell.branchinspect` (not all checks are
        executed, only keeps going until a spell inspection returns ``True``).
        """
        return any(spell.branchinspect(branch) for spell in self.spells)

    def branchentry(self, branch):
        """Run all spells."""
        # not using any: we want all entry code to be executed
        return bool([spell.branchentry(branch) for spell in self.spells])

    def branchexit(self, branch):
        for spell in self.spells:
             spell.branchexit(branch)

    def dataentry(self):
        """Look into every spell with :meth:`Spell.dataentry`."""
        self.spells = [spell for spell in self.spells
                       if spell.dataentry()]
        return bool(self.spells)

    def dataexit(self):
        """Look into every spell with :meth:`Spell.dataexit`."""
        for spell in self.spells:
            spell.dataexit()

    @property
    def changed(self):
        return any(spell.changed for spell in self.spells)

def SpellGroupSeries(*args):
    """Class factory for grouping spells in series."""
    return type("".join(spellclass.__name__ for spellclass in args),
                (SpellGroupSeriesBase,),
                {"SPELLCLASSES": args,
                 "SPELLNAME":
                     " | ".join(spellclass.SPELLNAME for spellclass in args),
                 "READONLY": 
                      all(spellclass.READONLY for spellclass in args)})

def SpellGroupParallel(*args):
    """Class factory for grouping spells in parallel."""
    return type("".join(spellclass.__name__ for spellclass in args),
                (SpellGroupParallelBase,),
                {"SPELLCLASSES": args,
                 "SPELLNAME":
                     " & ".join(spellclass.SPELLNAME for spellclass in args),
                 "READONLY": 
                      all(spellclass.READONLY for spellclass in args)})

class SpellApplyPatch(Spell):
    """A spell for applying a patch on files."""

    SPELLNAME = "applypatch"

    def datainspect(self):
        """There is no need to read the whole file, so we apply the patch
        already at inspection stage, and stop the spell process by returning
        ``False``.
    
        :return: ``False``
        :rtype: ``bool``
        """
        # get the patch command (if there is one)
        patchcmd = self.toaster.options["patchcmd"]
        if not patchcmd:
            raise ValueError("must specify a patch command")
        # first argument is always the stream, by convention
        oldfile = self.stream
        oldfilename = oldfile.name
        newfilename = oldfilename + ".patched"
        patchfilename = oldfilename + ".patch"
        self.toaster.msg("writing %s..." % newfilename)
        # close all files before calling external command
        oldfile.close()
        subprocess.call([patchcmd, oldfilename, newfilename, patchfilename])

        # do not go further, spell is done
        return False


class fake_logger:
    """Simple logger for testing."""
    level = logging.DEBUG

    @classmethod
    def _log(cls, level, level_str, msg):
        # do not actually log, just print
        if level >= cls.level:
            print("pyffi.toaster:%s:%s" % (level_str, msg))

    @classmethod
    def error(cls, msg):
        cls._log(logging.ERROR, "ERROR", msg)

    @classmethod
    def warn(cls, msg):
        cls._log(logging.WARNING, "WARNING", msg)

    @classmethod
    def info(cls, msg):
        cls._log(logging.INFO, "INFO", msg)

    @classmethod
    def debug(cls, msg):
        cls._log(logging.DEBUG, "DEBUG", msg)

    @classmethod
    def setLevel(cls, level):
        cls.level = level

def _toaster_job(args):
    """For multiprocessing. This function creates a new toaster, with the
    given options and spells, and calls the toaster on filename.
    """

    class multiprocessing_fake_logger(fake_logger):
        """Simple logger which works well along with multiprocessing
        on all platforms.
        """
        @classmethod
        def _log(cls, level, level_str, msg):
            # do not actually log, just print
            if level >= cls.level:
                print("pyffi.toaster:%i:%s:%s"
                      % (multiprocessing.current_process().pid,
                         level_str, msg))

    toasterclass, filename, options, spellnames = args
    toaster = toasterclass(options=options, spellnames=spellnames,
                           logger=multiprocessing_fake_logger)

    # toast entry code
    if not toaster.spellclass.toastentry(toaster):
        self.msg("spell does not apply! quiting early...")
        return

    # toast single file
    stream = open(filename, mode='rb' if toaster.spellclass.READONLY else 'r+b')
    toaster._toast(stream)

    # toast exit code
    toaster.spellclass.toastexit(toaster)

# CPU_COUNT is used for default number of jobs
if multiprocessing:
    try:
        CPU_COUNT = multiprocessing.cpu_count()
    except NotImplementedError:
        CPU_COUNT = 1
else:
    CPU_COUNT = 1

class Toaster(object):
    """Toaster base class. Toasters run spells on large quantities of files.
    They load each file and pass the data structure to any number of spells.
    """

    FILEFORMAT = pyffi.object_models.FileFormat
    """The file format class (a subclass of
    :class:`~pyffi.object_models.FileFormat`)."""

    SPELLS = []
    """List of all available :class:`~pyffi.spells.Spell` classes."""

    EXAMPLES = ""
    """Some examples which describe typical use of the toaster."""

    ALIASDICT = {}
    """Dictionary with aliases for spells."""

    DEFAULT_OPTIONS = dict(
        raisetesterror=False, verbose=1, pause=False,
        exclude=[], include=[], examples=False,
        spells=False,
        interactive=True,
        helpspell=False, dryrun=False, prefix="", suffix="", arg="",
        createpatch=False, applypatch=False, diffcmd="", patchcmd="",
        series=False,
        skip=[], only=[],
        jobs=CPU_COUNT, refresh=32,
        sourcedir="", destdir="",
        archives=False,
        resume=False,
        gccollect=False,
        inifile="")

    """List of spell classes of the particular :class:`Toaster` instance."""

    options = {}
    """The options of the toaster, as ``dict``."""

    spellnames = []
    """A list of the names of the spells."""

    top = ""
    """Name of the top folder to toast."""

    indent = 0
    """An ``int`` which describes the current indentation level for messages."""

    logger = logging.getLogger("pyffi.toaster")
    """A :class:`logging.Logger` for toaster log messages."""

    include_types = []
    """Tuple of types corresponding to the include key of :attr:`options`."""

    exclude_types = []
    """Tuple of types corresponding to the exclude key of :attr:`options`."""

    only_regexs = []
    """Tuple of regular expressions corresponding to the only key of
    :attr:`options`."""

    skip_regexs = []
    """Tuple of regular expressions corresponding to the skip key of
    :attr:`options`."""

    def __init__(self, spellclass=None, options=None, spellnames=None,
                 logger=None):
        """Initialize the toaster.

        :param spellclass: Deprecated, use spellnames.
        :type spellclass: :class:`Spell`
        :param options: The options (as keyword arguments).
        :type options: ``dict``
        :param spellnames: List of names of spells.
        :type spellnames: ``list`` of ``str``
        """
        self.options = deepcopy(self.DEFAULT_OPTIONS)
        self.spellnames = spellnames if spellnames else []
        if logger:
            # override default logger
            self.logger = logger
        if options:
            self.options.update(options)
        self.indent = 0
        # update options and spell class
        self._update_options()
        if spellnames:
            self._update_spellclass()
        else:
            # deprecated
            self.spellclass = spellclass
        # track which files toasted succesfully, and which did not
        self.files_done = {}
        self.files_skipped = set()
        self.files_failed = set()

    def _update_options(self):
        """Synchronize some fields with given options."""
        # set verbosity level (also of self.logger, in case of a custom one)
        if self.options["verbose"] <= 0:
            logging.getLogger("pyffi").setLevel(logging.WARNING)
            self.logger.setLevel(logging.WARNING)
        elif self.options["verbose"] == 1:
            logging.getLogger("pyffi").setLevel(logging.INFO)
            self.logger.setLevel(logging.INFO)
        else:
            logging.getLogger("pyffi").setLevel(logging.DEBUG)
            self.logger.setLevel(logging.DEBUG)
        # check errors
        if self.options["createpatch"] and self.options["applypatch"]:
            raise ValueError(
                "options --diff and --patch are mutually exclusive")
        if self.options["diffcmd"] and not(self.options["createpatch"]):
            raise ValueError(
                "option --diff-cmd can only be used with --diff")
        if self.options["patchcmd"] and not(self.options["applypatch"]):
            raise ValueError(
                "option --patch-cmd can only be used with --patch")
        # multiprocessing available?
        if (multiprocessing is None) and self.options["jobs"] > 1:
            self.logger.warn(
                "multiprocessing not supported on this platform")
            self.options["jobs"] = 1
        # update include and exclude types
        self.include_types = tuple(
            getattr(self.FILEFORMAT, block_type)
            for block_type in self.options["include"])
        self.exclude_types = tuple(
            getattr(self.FILEFORMAT, block_type)
            for block_type in self.options["exclude"])
        # update skip and only regular expressions
        self.skip_regexs = tuple(
            re.compile(regex) for regex in self.options["skip"])
        self.only_regexs = tuple(
            re.compile(regex) for regex in self.options["only"])

    def _update_spellclass(self):
        """Update spell class from given list of spell names."""
        # get spell classes
        spellclasses = []
        if not self.spellnames:
            raise ValueError("no spells specified")
        for spellname in self.spellnames:
            # convert old names
            if spellname in self.ALIASDICT:
                self.logger.warning(
                    "The %s spell is deprecated and will be removed"
                    " from a future release; use the %s spell as a"
                    " replacement" % (spellname, self.ALIASDICT[spellname]))
                spellname = self.ALIASDICT[spellname]
            # find the spell
            spellklasses = [spellclass for spellclass in self.SPELLS
                            if spellclass.SPELLNAME == spellname]
            if not spellklasses:
                raise ValueError(
                    "%s is not a known spell" % spellname)
            if len(spellklasses) > 1:
                raise ValueError(
                    "multiple spells are called %s (BUG?)" % spellname)
            spellclasses.extend(spellklasses)
        # create group of spells
        if len(spellclasses) > 1:
            if self.options["series"]:
                self.spellclass = SpellGroupSeries(*spellclasses)
            else:
                self.spellclass = SpellGroupParallel(*spellclasses)
        else:
            self.spellclass = spellclasses[0]

    def msg(self, message):
        """Write log message with :meth:`logger.info`, taking into account
        :attr:`indent`.

        :param message: The message to write.
        :type message: ``str``
        """
        for line in message.split("\n"):
            self.logger.info("  " * self.indent + line)

    def msgblockbegin(self, message):
        """Acts like :meth:`msg`, but also increases :attr:`indent` after writing the
        message."""
        self.msg(message)
        self.indent += 1

    def msgblockend(self, message=None):
        """Acts like :meth:`msg`, but also decreases :attr:`indent` before writing the
        message, but if the message argument is ``None``, then no message is
        printed."""
        self.indent -= 1
        if not(message is None):
            self.msg(message)

    def is_admissible_branch_class(self, branchtype):
        """Helper function which checks whether a given branch type should
        have spells cast on it or not, based in exclude and include options.

        >>> from pyffi.formats.nif import NifFormat
        >>> class MyToaster(Toaster):
        ...     FILEFORMAT = NifFormat
        >>> toaster = MyToaster() # no include or exclude: all admissible
        >>> toaster.is_admissible_branch_class(NifFormat.NiProperty)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiNode)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiAVObject)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiLODNode)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiMaterialProperty)
        True
        >>> toaster = MyToaster(options={"exclude": ["NiProperty", "NiNode"]})
        >>> toaster.is_admissible_branch_class(NifFormat.NiProperty)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiNode)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiAVObject)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiLODNode)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiMaterialProperty)
        False
        >>> toaster = MyToaster(options={"include": ["NiProperty", "NiNode"]})
        >>> toaster.is_admissible_branch_class(NifFormat.NiProperty)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiNode)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiAVObject)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiLODNode) # NiNodes are!
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiMaterialProperty) # NiProperties are!
        True
        >>> toaster = MyToaster(options={"include": ["NiProperty", "NiNode"], "exclude": ["NiMaterialProperty", "NiLODNode"]})
        >>> toaster.is_admissible_branch_class(NifFormat.NiProperty)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiNode)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiAVObject)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiLODNode)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiSwitchNode)
        True
        >>> toaster.is_admissible_branch_class(NifFormat.NiMaterialProperty)
        False
        >>> toaster.is_admissible_branch_class(NifFormat.NiAlphaProperty)
        True
        """
        #print("checking %s" % branchtype.__name__) # debug
        # check that block is not in exclude...
        if not issubclass(branchtype, self.exclude_types):
            # not excluded!
            # check if it is included
            if not self.include_types:
                # if no include list is given, then assume included by default
                # so, the block is admissible
                return True
            elif issubclass(branchtype, self.include_types):
                # included as well! the block is admissible
                return True
        # not admissible
        #print("not admissible") # debug
        return False

    @staticmethod
    def parse_inifile(option, opt, value, parser, toaster=None):
        r"""Initializes spell classes and options from an ini file.

        >>> import pyffi.spells.nif
        >>> import pyffi.spells.nif.modify
        >>> class NifToaster(pyffi.spells.nif.NifToaster):
        ...     SPELLS = [pyffi.spells.nif.modify.SpellDelBranches]
        >>> import tempfile
        >>> cfg = tempfile.NamedTemporaryFile(delete=False)
        >>> cfg.write("[main]\n")
        >>> cfg.write("spell = modify_delbranches\n")
        >>> cfg.write("folder = tests/nif/test_vertexcolor.nif\n")
        >>> cfg.write("[options]\n")
        >>> cfg.write("source-dir = tests/\n")
        >>> cfg.write("dest-dir = _tests/\n")
        >>> cfg.write("exclude = NiVertexColorProperty NiStencilProperty\n")
        >>> cfg.write("skip = 'testing quoted string'    normal_string\n")
        >>> cfg.close()
        >>> toaster = NifToaster(logger=fake_logger)
        >>> import sys
        >>> sys.argv = [
        ...     "niftoaster.py",
        ...     "--ini-file=utilities/toaster/default.ini",
        ...     "--ini-file=%s" % cfg.name,
        ...     "--noninteractive", "--jobs=1"]
        >>> toaster.cli()
        pyffi.toaster:INFO:=== tests/nif/test_vertexcolor.nif ===
        pyffi.toaster:INFO:  --- modify_delbranches ---
        pyffi.toaster:INFO:    ~~~ NiNode [Scene Root] ~~~
        pyffi.toaster:INFO:      ~~~ NiTriStrips [Cube] ~~~
        pyffi.toaster:INFO:        ~~~ NiStencilProperty [] ~~~
        pyffi.toaster:INFO:          stripping this branch
        pyffi.toaster:INFO:        ~~~ NiSpecularProperty [] ~~~
        pyffi.toaster:INFO:        ~~~ NiMaterialProperty [Material] ~~~
        pyffi.toaster:INFO:        ~~~ NiVertexColorProperty [] ~~~
        pyffi.toaster:INFO:          stripping this branch
        pyffi.toaster:INFO:        ~~~ NiTriStripsData [] ~~~
        pyffi.toaster:INFO:creating destination path _tests/nif
        pyffi.toaster:INFO:  writing _tests/nif/test_vertexcolor.nif
        pyffi.toaster:INFO:Finished.
        >>> import os
        >>> os.remove(cfg.name)
        >>> os.remove("_tests/nif/test_vertexcolor.nif")
        >>> os.rmdir("_tests/nif/")
        >>> os.rmdir("_tests/")
        >>> for name, value in sorted(toaster.options.items()):
        ...     print("%s: %s" % (name, value))
        applypatch: False
        archives: False
        arg: 
        createpatch: False
        destdir: _tests/
        diffcmd: 
        dryrun: False
        examples: False
        exclude: ['NiVertexColorProperty', 'NiStencilProperty']
        gccollect: False
        helpspell: False
        include: []
        inifile: 
        interactive: False
        jobs: 1
        only: []
        patchcmd: 
        pause: True
        prefix: 
        raisetesterror: False
        refresh: 32
        resume: True
        series: False
        skip: ['testing quoted string', 'normal_string']
        sourcedir: tests/
        spells: False
        suffix: 
        verbose: 1
        """
        ini_parser = ConfigParser()
        # read config file(s)
        ini_parser.read(value)
        # process all options
        if ini_parser.has_section("options"):
            for opt_str, opt_values in ini_parser.items("options"):
                option = parser._long_opt["--" + opt_str]
                for opt_value in shlex.split(opt_values):
                    option.process(opt_str, opt_value, parser.values, parser)
        # get spells and top folder
        if ini_parser.has_section("main"):
            if ini_parser.has_option("main", "spell"):
                toaster.spellnames.extend(ini_parser.get("main", "spell").split())
            if ini_parser.has_option("main", "folder"):
                toaster.top = ini_parser.get("main", "folder")

    def cli(self):
        """Command line interface: initializes spell classes and options from
        the command line, and run the :meth:`toast` method.
        """
        # parse options and positional arguments
        usage = "%prog [options] <spell1> <spell2> ... <file>|<folder>"
        description = (
            "Apply the spells <spell1>, <spell2>, and so on,"
            " on <file>, or recursively on <folder>.")
        errormessage_numargs = (
            "incorrect number of arguments (use the --help option for help)")

        parser = optparse.OptionParser(
            usage,
            version="%%prog (PyFFI %s)" % pyffi.__version__,
            description=description)
        parser.add_option(
            "--archives", dest="archives",
            action="store_true",
            help="also parse files inside archives")
        parser.add_option(
            "-a", "--arg", dest="arg",
            type="string",
            metavar="ARG",
            help="pass argument ARG to each spell")
        parser.add_option(
            "--dest-dir", dest="destdir",
            type="string",
            metavar="DESTDIR",
            help=
            "write files to DESTDIR"
            " instead of overwriting the original;"
            " this is done by replacing SOURCEDIR by DESTDIR"
            " in all source file paths")
        parser.add_option(
            "--diff", dest="createpatch",
            action="store_true",
            help=
            "write a binary patch"
            " instead of overwriting the original")
        parser.add_option(
            "--diff-cmd", dest="diffcmd",
            type="string",
            metavar="CMD",
            help=
            "use CMD as diff command; this command must accept precisely"
            " 3 arguments: 'CMD oldfile newfile patchfile'.")
        parser.add_option(
            "--dry-run", dest="dryrun",
            action="store_true",
            help=
            "save modification to temporary file"
            " instead of overwriting the original"
            " (for debugging)")
        parser.add_option(
            "--examples", dest="examples",
            action="store_true",
            help="show examples of usage and exit")
        parser.add_option(
            "--help-spell", dest="helpspell",
            action="store_true",
            help="show help specific to the given spells")
        parser.add_option(
            "-i", "--include", dest="include",
            type="string",
            action="append",
            metavar="BLOCK",
            help=
            "include only block type BLOCK in spell; if this option is"
            " not specified, then all block types are included except"
            " those specified under --exclude; include multiple block"
            " types by specifying this option more than once")
        parser.add_option(
            "--ini-file", dest="inifile",
            type="string",
            action="callback",
            callback=self.parse_inifile,
            callback_kwargs={'toaster': self},
            metavar="FILE",
            help=
            "read all options from FILE; if specified, all other arguments"
            " are ignored; to take options from multiple ini files, specify"
            " more than once")
        parser.add_option(
            "-j", "--jobs", dest="jobs",
            type="int",
            metavar="JOBS",
            help="allow JOBS jobs at once [default: %default]")
        parser.add_option(
            "--noninteractive", dest="interactive",
            action="store_false",
            help="non-interactive session (overwrites files without warning)")
        parser.add_option(
            "--only", dest="only",
            type="string",
            action="append",
            metavar="REGEX",
            help=
            "only toast files whose names"
            " (i) contain the regular expression REGEX, and"
            " (ii) do not contain any regular expression specified with --skip;"
            " if specified multiple times, the expressions are 'ored'")
        parser.add_option(
            "--overwrite", dest="resume",
            action="store_false",
            help="overwrite existing files (also see --resume)")
        parser.add_option(
            "--patch", dest="applypatch",
            action="store_true",
            help="apply all binary patches")
        parser.add_option(
            "--patch-cmd", dest="patchcmd",
            type="string",
            metavar="CMD",
            help=
            "use CMD as patch command; this command must accept precisely "
            "3 arguments: 'CMD oldfile newfile patchfile'.""")
        parser.add_option(
            "-p", "--pause", dest="pause",
            action="store_true",
            help="pause when done")
        parser.add_option(
            "--prefix", dest="prefix",
            type="string",
            metavar="PREFIX",
            help=
            "prepend PREFIX to file name when saving modification"
            " instead of overwriting the original")
        parser.add_option(
            "-r", "--raise", dest="raisetesterror",
            action="store_true",
            help="raise exception on errors during the spell (for debugging)")
        parser.add_option(
            "--refresh", dest="refresh",
            type="int",
            metavar="REFRESH",
            help=
            "start new process pool every JOBS * REFRESH files"
            " if JOBS is 2 or more"
            " (when processing a large number of files, this prevents"
            " leaking memory on some operating systems) [default: %default]")
        parser.add_option(
            "--resume", dest="resume",
            action="store_true",
            help="do not overwrite existing files")
        parser.add_option(
            "--series", dest="series",
            action="store_true",
            help="run spells in series rather than in parallel")
        parser.add_option(
            "--skip", dest="skip",
            type="string",
            action="append",
            metavar="REGEX",
            help=
            "skip all files whose names contain the regular expression REGEX"
            " (takes precedence over --only);"
            " if specified multiple times, the expressions are 'ored'")
        parser.add_option(
            "--source-dir", dest="sourcedir",
            type="string",
            metavar="SOURCEDIR",
            help=
            "see --dest-dir")
        parser.add_option(
            "--spells", dest="spells",
            action="store_true",
            help="list all spells and exit")
        parser.add_option(
            "--suffix", dest="suffix",
            type="string",
            metavar="SUFFIX",
            help="append SUFFIX to file name when saving modification"
            " instead of overwriting the original")
        parser.add_option(
            "-v", "--verbose", dest="verbose",
            type="int",
            metavar="LEVEL",
            help="verbosity level: 0, 1, or 2 [default: %default]")
        parser.add_option(
            "-x", "--exclude", dest="exclude",
            type="string",
            action="append",
            metavar="BLOCK",
            help=
            "exclude block type BLOCK from spell; exclude multiple"
            " block types by specifying this option more than once")
        parser.add_option(
            "--gccollect", dest="gccollect",
            action="store_true",
            help=
            "run garbage collector after every spell"
            " (slows down toaster but may save memory)")
        parser.set_defaults(**deepcopy(self.DEFAULT_OPTIONS))
        (options, args) = parser.parse_args()

        # convert options to dictionary
        self.options = {}
        for optionname in dir(options):
            # skip default attributes of optparse.Values
            if optionname not in dir(optparse.Values):
                self.options[optionname] = getattr(options, optionname)

        # update options
        self._update_options()

        # check if we had examples and/or spells: quit
        if options.spells:
            for spellclass in self.SPELLS:
                print(spellclass.SPELLNAME)
            return
        if options.examples:
            print(self.EXAMPLES)
            return

        # check if we are applying patches
        if options.applypatch:
            if len(args) > 1:
                parser.error("when using --patch, do not specify a spell")
            # set spell class to applying patch
            self.spellclass = SpellApplyPatch
            # set top
            if args:
                self.top = args[-1]
            elif not self.top:
                parser.error("no folder or file specified")
        else:
            # get spell names and top
            if options.helpspell:
                # special case: --spell-help would not have a top specified
                self.spellnames = args[:]
                self._update_spellclass()
                self.msg(self.spellclass.__doc__)
                return
            if not args:
                # no args: error if no top or no spells
                if not(self.top and self.spellnames):
                    parser.error(errormessage_numargs)
            elif len(args) == 1:
                # single argument is top, error if no spells
                if not(self.spellnames):
                    parser.error(errormessage_numargs)
                self.top = args[-1]
            else:
                # all arguments, except the last one, are spells
                self.spellnames.extend(args[:-1])
                # last argument is top
                self.top = args[-1]
            # update the spell class
            self._update_spellclass()

        if not self.options["archives"]:
            self.toast(self.top)
        else:
            self.toast_archives(self.top)

        # signal the end
        self.logger.info("Finished.")
        if options.pause and options.interactive:
            raw_input("Press enter...")

    def inspect_filename(self, filename):
        """Returns whether to toast a filename or not, based on
        skip_regexs and only_regexs.
        """
        if any(regex.search(filename) for regex in self.skip_regexs):
            # found some --skip regex, so do not toast
            return False
        if not self.only_regexs:
            # --only not specified: then by default take all files
            return True
        if any(regex.search(filename) for regex in self.only_regexs):
            # found at least one --only regex, so toast
            return True
        else:
            # no --only found, so do not toast
            return False

    def toast(self, top):
        """Walk over all files in a directory tree and cast spells
        on every file.

        :param top: The directory or file to toast.
        :type top: str
        """

        def file_pools(chunksize):
            """Helper function which generates list of files, sorted by size,
            in chunks of given size.
            """
            all_files = pyffi.utils.walk(
                top, onerror=None,
                re_filename=self.FILEFORMAT.RE_FILENAME)
            while True:
                # fetch chunksize files from all files
                file_pool = [
                    filename for i, filename in izip(
                        xrange(chunksize), all_files)]
                if not file_pool:
                    # done!
                    break
                # sort files by size
                file_pool.sort(key=os.path.getsize, reverse=True)
                yield file_pool

        # toast entry code
        if not self.spellclass.toastentry(self):
            self.msg("spell does not apply! quiting early...")
            return

        # some defaults are different from the defaults defined in
        # the cli function: these defaults are reasonable for when the
        # toaster is called NOT from the command line
        # whereas the cli function defines defaults that are reasonable
        # when the toaster is called from the command line
        # in particular, when calling from the command line, the script
        # is much more verbose by default

        pause = self.options.get("pause", False)
        
        # do not ask for confirmation (!= cli default)
        interactive = self.options.get("interactive", False)

        dryrun = self.options.get("dryrun", False)
        prefix = self.options.get("prefix", "")
        suffix = self.options.get("suffix", "")
        destdir = self.options.get("destdir", "")
        sourcedir = self.options.get("sourcedir", "")
        createpatch = self.options.get("createpatch", False)
        applypatch = self.options.get("applypatch", False)
        jobs = self.options.get("jobs", CPU_COUNT)

        # get source directory if not specified
        if not sourcedir:
            # set default source directory
            if os.path.isfile(top):
                sourcedir = os.path.dirname(top)
            else:
                sourcedir = top
            # store the option (so spells can use it)
            self.options["sourcedir"] = sourcedir

        # check that top starts with sourcedir
        if not top.startswith(sourcedir):
            raise ValueError(
                "invalid --source-dir: %s does not start with %s"
                % (top, sourcedir))

        # warning
        if ((not self.spellclass.READONLY) and (not dryrun)
            and (not prefix) and (not createpatch)
            and interactive and (not suffix) and (not destdir)):
            print("""\
This script will modify your files, in particular if something goes wrong it
may destroy them. Make a backup of your files before running this script.
""")
            if not raw_input(
                "Are you sure that you want to proceed? [n/y] ") in ("y", "Y"):
                self.logger.info("Script aborted by user.")
                if pause:
                    raw_input("Press enter...")
                return

        # walk over all streams, and create a data instance for each of them
        # inspect the file but do not yet read in full
        if jobs == 1:
            for stream in self.FILEFORMAT.walk(
                top, mode='rb' if self.spellclass.READONLY else 'r+b'):
                self._toast(stream)
                if self.options["gccollect"]:
                    # force free memory (helps when parsing many files)
                    gc.collect()
        else:
            chunksize = self.options["refresh"] * self.options["jobs"]
            self.msg("toasting with %i threads in chunks of %i files"
                     % (jobs, chunksize))
            for file_pool in file_pools(chunksize):
                self.logger.debug("process file pool:")
                for filename in file_pool:
                    self.logger.debug("  " + filename)
                pool = multiprocessing.Pool(processes=jobs)
                # force chunksize=1 for the pool
                # this makes sure that the largest files (which come first
                # in the pool) are processed in parallel
                result = pool.map_async(
                    _toaster_job,
                    ((self.__class__, filename, self.options, self.spellnames)
                     for filename in file_pool),
                    chunksize=1)
                # specify timeout, so CTRL-C works
                # 99999999 is about 3 years, should be long enough... :-)
                result.wait(timeout=99999999)
                pool.close()
                pool.join()

        # toast exit code
        self.spellclass.toastexit(self)

    def toast_archives(self, top):
        """Toast all files in all archives."""
        if not self.FILEFORMAT.ARCHIVE_CLASSES:
            self.logger.info("No known archives contain this file format.")
        # walk over all files, and pick archives as we go
        for filename_in in pyffi.utils.walk(top):
            for ARCHIVE_CLASS in self.FILEFORMAT.ARCHIVE_CLASSES:
                # check if extension matches
                if not ARCHIVE_CLASS.RE_FILENAME.match(filename_in):
                    continue
                # open the archive
                try:
                    archive_in = ARCHIVE_CLASS.Data(name=filename_in, mode='r')
                except ValueError:
                    self.logger.warn("archive format not recognized, skipped")
                    continue
                # toast all members in the archive
                # and save them to a temporary archive as we go
                if not self.spellclass.READONLY:
                    for member in archive_in.get_members():
                        self._toast_member(member)
                else:
                    file_out = tempfile.TemporaryFile()
                    archive_out = ARCHIVE_CLASS.Data(fileobj=file_out, mode='w')
                    for member in archive_in.get_members():
                        self._toast(member)
                        archive_out.add(member)
                    archive_out.close()
                archive_in.close()

    def _toast(self, stream):
        """Run toaster on particular stream and data.
        Used as helper function.
        """
        # inspect the file name
        if not self.inspect_filename(stream.name):
            self.msg("=== %s (skipped) ===" % stream.name)
            self.files_skipped.add(stream.name)
            return

        # check if file exists
        if self.options["resume"]:
            if self.spellclass.get_toast_stream(
                self, stream.name, test_exists=True):
                self.msg("=== %s (already done) ===" % stream.name)
                return

        data = self.FILEFORMAT.Data()

        self.msgblockbegin("=== %s ===" % stream.name)
        try:
            # inspect the file (reads only the header)
            data.inspect(stream)

            # create spell instance
            spell = self.spellclass(toaster=self, data=data, stream=stream)
            
            # inspect the spell instance
            if spell._datainspect() and spell.datainspect():
                # read the full file
                data.read(stream)
                
                # cast the spell on the data tree
                spell.recurse()

                # save file back to disk if not readonly and the spell
                # changed the file
                if (not self.spellclass.READONLY) and spell.changed:
                    if self.options["createpatch"]:
                        self.writepatch(stream, data)
                    else:
                        self.write(stream, data)
            self.files_done[stream.name] = spell.reports

        except Exception:
            self.files_failed.add(stream.name)
            self.logger.error("TEST FAILED ON %s" % stream.name)
            self.logger.error(
                "If you were running a spell that came with PyFFI, then")
            self.logger.error(
                "please report this as a bug (include the file) on")
            self.logger.error(
                "http://sourceforge.net/tracker/?group_id=199269")
            # if raising test errors, reraise the exception
            if self.options["raisetesterror"]:
                raise
        finally:
            self.msgblockend()

    def get_toast_head_root_ext(self, filename):
        """Get the name of where the input file *filename* would
        be written to by the toaster: head, root, and extension.

        :param filename: The name of the hypothetical file to be
            toasted.
        :type filename: :class:`str`
        :return: The head, root, and extension of the destination, or
            ``(None, None, None)`` if ``--dry-run`` is specified.
        :rtype: :class:`tuple` of three :class:`str`\ s
        """
        # first cover trivial case
        if self.options["dryrun"]:
            return (None, None, None)
        # split original file up
        head, tail = os.path.split(filename)
        root, ext = os.path.splitext(tail)
        # check if head sourcedir needs replacing by destdir
        # and do some sanity checks if this is the case
        if self.options["destdir"]:
            if not self.options["sourcedir"]:
                raise ValueError(
                    "--dest-dir specified without --source-dir")
            if not head.startswith(self.options["sourcedir"]):
                raise ValueError(
                    "invalid --source-dir: %s does not start with %s"
                    % (filename, self.options["sourcedir"]))
            head = head.replace(
                self.options["sourcedir"], self.options["destdir"], 1)
        return (
            head,
            self.options["prefix"] + root + self.options["suffix"],
            ext,
            )

    def get_toast_stream(self, filename, test_exists=False):
        """Calls :meth:`get_toast_head_root_ext(filename)`
        to determine the name of the toast file, and return
        a stream for writing accordingly.

        Then return a stream where result can be written to, or
        in case test_exists is True, test if result would overwrite a
        file. More specifically, if test_exists is True, then no
        streams are created, and True is returned if the file
        already exists, and False is returned otherwise.
        """
        if self.options["dryrun"]:
            if test_exists:
                return False # temporary file never exists
            else:
                self.msg("writing to temporary file")
                return tempfile.TemporaryFile()
        head, root, ext = self.get_toast_head_root_ext(filename)
        if not os.path.exists(head):
            if test_exists:
                # path does not exist, so file definitely does
                # not exist
                return False
            else:
                self.logger.info("creating destination path %s" % head)
                os.makedirs(head)
        filename =  os.path.join(head, root + ext)
        if test_exists:
            return os.path.exists(filename)
        else:
            if os.path.exists(filename):
                self.msg("overwriting %s" % filename)
            else:
                self.msg("writing %s" % filename)
            return open(filename, "wb")

    def write(self, stream, data):
        """Writes the data to data and raises an exception if the
        write fails, but restores file if fails on overwrite.
        """
        outstream = self.spellclass.get_toast_stream(self, stream.name)
        if stream is outstream:
            # make backup
            stream.seek(0)
            backup = stream.read(-1)
            stream.seek(0)
        try:
            try:
                data.write(outstream)
            except: # not just Exception, also CTRL-C
                self.msg("write failed!!!")
                if stream is outstream:
                    self.msg("attempting to restore original file...")
                    stream.seek(0)
                    stream.write(backup)
                    stream.truncate()
                else:
                    outstream_name = outstream.name
                    self.msg("removing incompletely written file...")
                    outstream.close()
                    # temporary streams are removed on close
                    # so check if it exists before removing
                    if os.path.exists(outstream_name):
                        os.remove(outstream_name)
                raise
            if stream is outstream:
                stream.truncate()
        finally:
            outstream.close()

    def writepatch(self, stream, data):
        """Creates a binary patch for the updated file."""
        diffcmd = self.options.get('diffcmd')
        if not diffcmd:
            raise ValueError("must specify a diff command")


        # create a temporary file that won't get deleted when closed
        self.options["suffix"] = ".tmp"
        newfile = self.spellclass.get_toast_stream(self, stream.name)
        try:
            data.write(newfile)
        except: # not just Exception, also CTRL-C
            self.msg("write failed!!!")
            raise
        # use external diff command
        oldfile = stream
        oldfilename = oldfile.name
        patchfilename = newfile.name[:-4] + ".patch"
        # close all files before calling external command
        oldfile.close()
        newfile.close()
        self.msg("calling %s" % diffcmd)
        subprocess.call([diffcmd, oldfilename, newfilename, patchfilename])
        # delete temporary file
        os.remove(newfilename)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
