'''
FBXPostScript
This script allows custom import operations for consistent development.
Ex: Exporting a mesh from a UE4 level and putting it into Houdini's unit system
with the cuurect orientation.

NOTE: As of right now, the developer needs to add the required strings here
AND in FBXImport.

def CustomUI()
This tells the main window what to add to the end.

def PostScriptAdjust()
This is the script that gets called from FBXImport. It adds the required string
into the second parameter.

def ...()
These are custom functions defined by the developer.

TODO: Tuple string of functions for FBXImport to reference. This is to eliminate
the need to work in multiple files. FBXImport SHOULD check for what functions
are available here.
'''

import hou
import re

from PySide import QtGui

def CustomUI():
    CUSTOM_WIDGETS = []
    CUSTOM_WIDGETS.insert(0, QtGui.QLabel("Post Script Options"))
    CUSTOM_WIDGETS.insert(1, [QtGui.QLabel("Compatibility"),
                    QtGui.QComboBox()])
    CUSTOM_WIDGETS[1][1].insertItems(0, ["Unreal Engine 4",
                                "Maya"])

    return CUSTOM_WIDGETS

def PostScriptAdjust(BASE_WIDGETS=[], CUSTOM_WIDGETS=[]):
    # for index in range (0, len(CUSTOM_WIDGETS)):
    #     print CUSTOM_WIDGETS[index]

    sEngineCompat = CUSTOM_WIDGETS[1][1].currentText()

    if "Unreal Engine 4" in sEngineCompat:
        CompatUnrealEngine(BASE_WIDGETS, CUSTOM_WIDGETS)
    elif "Maya" in sEngineCompat:
        CompatMaya(BASE_WIDGETS, CUSTOM_WIDGETS)

#Custom functions
def CompatUnrealEngine(BASE_WIDGETS, CUSTOM_WIDGET):
    sFBXFile = BASE_WIDGETS[0][1].text()
    sFBXFile = sFBXFile[sFBXFile.rfind("/")+1:].replace(".","_")

    # Retreive FBX node
    nodeFBX = hou.node("/obj/" + sFBXFile)
    nodeChildren = nodeFBX.children()

    nodeParent = GetOriginNode(nodeChildren)

    for index in range(0,len(nodeChildren)):
        if(nodeChildren[index] != nodeParent and nodeChildren[index].type().name() == "geo"):
            nodeChildren[index].setParms({"keeppos":True})
            nodeChildren[index].setFirstInput(nodeParent)

    nodeParent.setParms({"tx":0, "ty":0, "tz":0,
                        "rx":-90, "ry":0, "rz":0,
                        "sx":0.01, "sy":0.01, "sz":0.01,
                        "px":0, "py":0, "pz":0})

    nodeFBX.layoutChildren()

    for index in range(0,len(nodeChildren)):
        if(nodeChildren[index] != nodeParent and nodeChildren[index].type().name() == "geo"):
            nodeChildren[index].setFirstInput(None)

    nodeParent.setParms({"tx":0, "ty":0, "tz":0,
                        "rx":0, "ry":0, "rz":0,
                        "sx":1, "sy":1, "sz":1,
                        "px":0, "py":0, "pz":0})

    reference = nodeParent.createNode("attribcreate::2.0", "ADD_ATTRIB_REFERENCE")
    reference.setFirstInput(nodeParent.displayNode())
    reference.setParms({"name1":"REFERENCE_MODEL",
                        "class1":"detail",
                        "type1":"int"})

    xform = nodeParent.createNode("xform","SET_TRANSFORM")
    xform.setFirstInput(reference)
    xform.setDisplayFlag(True)
    xform.setRenderFlag(True)

    xform.setParms({"tx":0, "ty":0, "tz":0,
                    "rx":-90, "ry":0, "rz":0,
                    "sx":0.01, "sy":0.01, "sz":0.01,
                    "px":0, "py":0, "pz":0})


    nodeParent.layoutChildren()

def CompatMaya(BASE_WIDGETS, CUSTOM_WIDGET):
    sFBXFile = BASE_WIDGETS[0][1].text()
    sFBXFile = sFBXFile[sFBXFile.rfind("/")+1:].replace(".","_")

    # Retreive FBX node
    nodeFBX = hou.node("/obj/" + sFBXFile)
    nodeChildren = nodeFBX.children()

    nodeParent = GetOriginNode(nodeChildren)

    for index in range(0,len(nodeChildren)):
        if(nodeChildren[index] != nodeParent and nodeChildren[index].type().name() == "geo"):
            nodeChildren[index].setParms({"keeppos":True})
            nodeChildren[index].setFirstInput(nodeParent)

    nodeParent.setParms({"tx":0, "ty":0, "tz":0,
                        "rx":-90, "ry":0, "rz":0,
                        "sx":0.01, "sy":0.01, "sz":0.01,
                        "px":0, "py":0, "pz":0})

    for index in range(0,len(nodeChildren)):
        nodeChildren[index].setFirstInput()

    nodeFBX.layoutChildren()

def GetOriginNode(nodes):
    strFBXChildren = []
    for index in range(0,len(nodes)):
        strFBXChildren.append(nodes[index].name())

    result = QtGui.QInputDialog.getItem(None,"Select Node", "Choose Origin Node", strFBXChildren)

    nodeParent = None
    for index in range(0,len(strFBXChildren)):
        if result[0] in strFBXChildren[index]:
            nodeParent = nodes[index]

    return nodeParent
