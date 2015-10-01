#!/usr/bin/python

"""The qskope script visualizes the structure of PyFFI structures and arrays."""

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

# check if PyQt4 is installed
try:
    from PyQt4 import QtGui
except ImportError:
    raw_input("""PyQt4 not found. Please download and install from

  http://www.riverbankcomputing.co.uk/software/pyqt/download""")
    raise

# import the main QSkope window class
from pyffi.qskope import QSkope

# system and option parsing functions
import sys
from optparse import OptionParser

# main script function
def main():
    """The main script function. Does argument parsing, file type checking,
    and builds the qskope interface."""
    # parse options and positional arguments
    usage = "%prog [options] [<file>]"
    description = """Parse and display the file <file>."""

    parser = OptionParser(usage,
                          version = "%prog $Rev$",
                          description = description)
    (options, args) = parser.parse_args()

    if len(args) > 1:
        parser.error("incorrect number of arguments (one at most)")

    # run the application
    app = QtGui.QApplication(sys.argv)
    mainwindow = QSkope()
    if len(args) >= 1:
        mainwindow.openFile(filename = args[0])
    mainwindow.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # set up logger
    logger = logging.getLogger("pyffi")
    logger.setLevel(logging.DEBUG)
    loghandler = logging.StreamHandler()
    loghandler.setLevel(logging.DEBUG)
    logformatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s")
    loghandler.setFormatter(logformatter)
    logger.addHandler(loghandler)
    # run main program
    main()
