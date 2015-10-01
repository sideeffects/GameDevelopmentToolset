Requirements
============

To run PyFFI's graphical file editor QSkope, you need 
`PyQt4 <http://www.riverbankcomputing.co.uk/software/pyqt/download>`_.

Using the Windows installer
===========================

Simply download and run the `Windows installer
<http://sourceforge.net/project/platformdownload.php?group_id=199269&sel_platform=3089>`_.

Manual installation
===================

If you install PyFFI manually, and you already have an older version
of PyFFI installed, then you **must** uninstall (see :ref:`uninstall`)
the old version before installing the new one.

Installing via setuptools
-------------------------

If you have `setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
installed, simply run::

  easy_install -U PyFFI

at the command prompt.

Installing from source package
------------------------------

First, get the `source package
<http://sourceforge.net/project/platformdownload.php?group_id=199269&sel_platform=5359>`_.
Untar or unzip the source package via either::

  tar xfvz PyFFI-x.x.x.tar.gz

or::

  unzip PyFFI-x.x.x.zip 

Change to the PyFFI directory and run the setup script::

  cd PyFFI-x.x.x
  python setup.py install



.. _uninstall:

Uninstall
=========

You can uninstall PyFFI manually simply by deleting the :file:`pyffi`
folder from your Python's :file:`site-packages` folder, which is typically
at::

  C:\Python25\Lib\site-packages\pyffi

or::

  /usr/lib/python2.5/site-packages/pyffi
