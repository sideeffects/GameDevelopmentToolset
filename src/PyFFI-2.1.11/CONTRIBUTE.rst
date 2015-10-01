How to contribute
*****************

Do you want to fix a bug, improve documentation, or add a new feature?

Get git/msysgit
===============

If you are on windows, you need `msysgit
<http://code.google.com/p/msysgit/downloads/list>`_.  If you are already familiar
with subversion, then, in a nutshell, msysgit is for git what
TortoiseSVN is for subversion. The main difference is that msysgit is
a command line based tool.

For more information about git and github, the `github help site
<http://help.github.com>`_ is a great start.

Track the source
================

If you simply want to keep track of the latest source code, start a
shell (or, the Git Bash on windows), and type (this is like "svn checkout")::

  git clone git://github.com/amorilia/pyffi.git

To synchronize your code, type (this is like "svn update")::

  git pull

Development
===========

Create a fork
-------------

* Get a `github account <https://github.com/signup/free>`_.

* `Log in <https://github.com/login>`_ on github and `fork PyFFI
  <http://help.github.com/forking>`_
  (yes! merging with git is easy so forking is encouraged!).

Use the source
--------------

PyFFI is entirely written in pure Python, hence the source code runs
as such on any system that runs Python. Edit the code with your
favorite editor, and install your version of PyFFI into your Python
tree to enable your PyFFI to be used by other applications such as for
instance QSkope, or the Blender NIF Scripts. From within your PyFFI
git checkout::

  C:\Python25\python.exe setup.py install

or on linux::

  python setup.py install

To build the documentation::

  cd docs-sphinx
  make html

PyFFI has an extensive test suite, which you can run via::

  python rundoctest.py

The Blender NIF Scripts test suite provides additional testing for
PyFFI. From within your niftools/blender checkout::

  ./install.sh
  blender -P runtest_xxx.py

To build the source packages and the Windows installer (on a linux
system which has both wine and nsis installed)::

  makezip.sh

Submit your updates
-------------------

Simply do a `pull request <http://help.github.com/pull-requests>`_
if you want your fork to be merged, and your contributions may be
included in the next release!
