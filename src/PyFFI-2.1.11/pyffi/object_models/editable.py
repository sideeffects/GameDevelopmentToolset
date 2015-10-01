"""Implements abstract editor base classes.

These abstract base classes provide an abstract layer for editing data in a
graphical user interface.

@todo: Make these into true abstract base classes, and implement and use the
    get_editor_value and set_editor_value functions in non-abstract derived
    classes.
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

class EditableBase(object):
    """The base class for all delegates."""
    def get_editor_value(self):
        """Return data as a value to initialize an editor with.
        Override this method.

        :return: A value for the editor.
        :rtype: any (whatever is appropriate for the particular
            implementation of the editor)
        """
        raise NotImplementedError

    def set_editor_value(self, editorvalue):
        """Set data from the editor value. Override this method.

        :param editorvalue: The value of the editor.
        :type editorvalue: any (whatever is appropriate for the particular
            implementation of the editor)
        """
        raise NotImplementedError

class EditableSpinBox(EditableBase):
    """Abstract base class for data that can be edited with a spin box that
    contains an integer. Override get_editor_minimum and get_editor_maximum to
    set the minimum and maximum values that the spin box may contain.

    Requirement: get_editor_value must return an ``int``, set_editor_value
    must take an ``int``.
    """
    def get_editor_value(self):
        return self.get_value()

    def set_editor_value(self, editorvalue):
        self.set_value(self, editorvalue)

    def get_editor_minimum(self):
        return -0x80000000

    def get_editor_maximum(self):
        return 0x7fffffff

class EditableFloatSpinBox(EditableSpinBox):
    """Abstract base class for data that can be edited with a spin box that
    contains a float. Override get_editor_decimals to set the number of decimals
    in the editor display.

    Requirement: get_editor_value must return a ``float``, set_editor_value
    must take a ``float``.
    """

    def get_editor_decimals(self):
        return 5

class EditableLineEdit(EditableBase):
    """Abstract base class for data that can be edited with a single line
    editor.

    Requirement: get_editor_value must return a ``str``, set_editor_value
    must take a ``str``.
    """
    pass

class EditableTextEdit(EditableLineEdit):
    """Abstract base class for data that can be edited with a multiline editor.

    Requirement:  get_editor_value must return a ``str``, set_editor_value
    must take a ``str``.
    """
    pass

class EditableComboBox(EditableBase):
    """Abstract base class for data that can be edited with combo boxes.
    This can be used for for instance enum types.

    Requirement: get_editor_value must return an ``int``, set_editor_value
    must take an ``int`` (this integer is the index in the list of keys).
    """

    def get_editor_keys(self):
        """Tuple of strings, each string describing an item."""
        return ()

class EditableBoolComboBox(EditableComboBox):
    """Class for data that can be edited with a bool combo box.

    Requirement: get_value must return a ``bool``, set_value must take a ``bool``.
    """
    def get_editor_keys(self):
        return ("False", "True")

    def set_editor_value(self, editorvalue):
        if editorvalue == 0:
            self.set_value(False)
        elif editorvalue == 1:
            self.set_value(True)
        else:
            raise ValueError("no value for index %i" % editorvalue)

    def get_editor_value(self):
        return 1 if self.get_value() else 0

