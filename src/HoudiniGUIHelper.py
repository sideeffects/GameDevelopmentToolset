'''
HoudiniGUIHelper
This file is a series of helper functions in creating UI tools for Houdini.
'''

def GenerateCommandString(FBX_OPTIONS):
    TEMP = ""
    for key, value in FBX_OPTIONS.iteritems():
        TEMP += key + " \'{}\' ".format(value)
    return TEMP

def GenerateRowWidget(WidgetArray):
    ROW = QtGui.QHBoxLayout()

    if isinstance(WidgetArray, list):
        for index in range(0,len(WidgetArray)):
            ROW.addWidget(WidgetArray[index])
    else:
        ROW.addWidget(WidgetArray)

    return ROW

def GetComboBoxIndex(FBX_OPTIONS, STRING_OPTION):
    return 1 if FBX_OPTIONS[STRING_OPTION] == 'on' else 0

def GetFBXCheckState(FBX_UNLOCK_MASK, FBX_OPTIONS, STRING_OPTION, BIT_MASK=0b0):
    if STRING_OPTION in '-u': #Unlock nodes?
        temp = FBX_UNLOCK_MASK[FBX_OPTIONS[STRING_OPTION]]
        return QtCore.Qt.Checked if temp*BIT_MASK else QtCore.Qt.Unchecked
    return QtCore.Qt.Checked if FBX_OPTIONS[STRING_OPTION] == 'on' else QtCore.Qt.Unchecked

def GetLineEditText(FBX_OPTIONS, STRING_OPTION):
    return FBX_OPTIONS[STRING_OPTION]
