'''
FBXImport

This script is a basic FBX importer modeled around Houdini's importer. Houdini's
importer doesn't really allow the ability to attach post-scripts. Why do we need
those? It allows the Houdini user to bring in models from other software
packages and convert it to Houdini's unit and orientation.

This custom version first hooks into FBXCustomUI. After the generated widgets,
this script generates more through FBXCustomUI.
'''

import hou
from PySide import QtCore
from PySide import QtGui
import FBXImportUI
reload(FBXImportUI)
from FBXImportUI import CustomUI

import FBXPostScript
reload(FBXPostScript)
from FBXPostScript import PostScriptAdjust
from FBXPostScript import CompatUnrealEngine

class CustomImport(QtGui.QWidget):
    WINDOW_LAYOUT   = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    INDEX           = 0
    CSS             = hou.expandString('$HOUDINI_USER_PREF_DIR') + "/toolbar/src/RealTimeVFX.qss"
    FBX_FILE        = hou.expandString('$HIP')
    WIDGETS         = []
    CUSTOM_WIDGETS  = []

    WIDGET_FBX_INPUT    = QtGui.QLineEdit()

    FBX_OPTIONS     =   {
                        '-f':'24',      #[int]              FPS
                        '-o':'off',     #[on|off]           Import directly into /obj
                        '-p':'rel',     #[abs|rel]          File paths absolute to relative
                        '-u':'all',     #[node|geo|def|all] What nodes will be unlocked?
                        '-t':'off',     #[on|off]           Force triangulation on NURBS and patch surfaces?
                        '-s':'vex',     #[vex|vop]          Import materials as VEX FBX or VOP networks?
                        '-v':'double',  #[float|double]     Vertex Caches as single or double precision types
                        '-c':'on',      #[on|off]           Import Camera
                        '-g':'on',      #[on|off]           Import Geometry
                        '-j':'on',      #[on|off]           Import Joints and skin objects
                        '-k':'off',     #[on|off]           Import Keyframe animations
                        '-l':'on',      #[on|off]           Import Light objects
                        '-m':'on',      #[on|off]           Import Textures and materialws
                        #'-a':'off',     #[maya|off]         Compatible with Maya or FBX Standard?
                        #'-b':'off',     #[on|off]           Blend deformers as Blend SOPs?
                        #'-h':'off',     #[on|off]           Hide joints attached to skin?
                        #'-i':'on',      #[on|off]           Import null nodes as subnets?
                        #'-r':'off',     #[on|off]           Resample cubic curves? If on, set -q!
                        #'-q':'1.0'      #[on|off]           Number of frames between each sample
                        }

    FBX_UNLOCK_MASK =   {
                        'none':0b00,
                        'geo':0b01,
                        'def':0b10,
                        'all':0b11,
                        0b00:'none',
                        0b01:'geo',
                        0b10:'def',
                        0b11:'all'
                        }

    def __init__(self, parent=None):
        app = QtGui.QWidget.__init__(self, parent)

        self.CUSTOM_WIDGETS = CustomUI()
        self.GenerateWindow()

    def GenerateWindow(self):
        self.setWindowTitle("Custom FBX Importer")
        self.setGeometry(1024, 512, 400, 512)

        CSS_FILE = QtCore.QFile(self.CSS)
        CSS_FILE.open(QtCore.QFile.ReadOnly)
        CSS_RESULT = CSS_FILE.readAll()
        self.setStyleSheet(CSS_RESULT.data())

        self.GenerateOptions()

    def AutoInsert(self):
        self.INDEX = self.INDEX + 1
        return self.INDEX - 1

    def GenerateRowWidget(self, WidgetArray):
        ROW = QtGui.QHBoxLayout()

        if isinstance(WidgetArray, list):
            for index in range(0,len(WidgetArray)):
                ROW.addWidget(WidgetArray[index])
        else:
            ROW.addWidget(WidgetArray)

        return ROW

    def ShowWidgetsFileDialog(self):
        TEMP = hou.ui.selectFile(self.FBX_FILE, "Select FBX File", False, hou.fileType.Any, "*.fbx")
        self.WIDGET_FBX_INPUT.setText(TEMP)

    def GenerateCommandString(self):
        TEMP = ""
        for key, value in self.FBX_OPTIONS.iteritems():
            TEMP += key + " " + "\'" + value + "\'" + " "
        return TEMP

    def ImportFBX(self):
        BASE = "fbximport "
        COMMANDS = self.GenerateCommandString()
        FILE = "\"" + self.WIDGET_FBX_INPUT.text() + "\""
        hou.hscript(BASE + COMMANDS + FILE)
        reload(FBXPostScript)
        from FBXPostScript import PostScriptAdjust
        from FBXPostScript import CompatUnrealEngine
        PostScriptAdjust(self.WIDGETS, self.CUSTOM_WIDGETS)

    def ImportFBXNewScene(self):
        BASE = "fbximport "
        COMMANDS = "-n " + self.GenerateCommandString()
        FILE = "\"" + self.WIDGET_FBX_INPUT.text() + "\""
        hou.hscript(BASE + COMMANDS + FILE)
        reload(FBXPostScript)
        from FBXPostScript import PostScriptAdjust
        from FBXPostScript import CompatUnrealEngine
        PostScriptAdjust(self.WIDGETS, self.CUSTOM_WIDGETS)

    #####################
    #CHECK BOXES
    #####################
    def GetFBXCheckState(self, STRING_OPTION, BIT_MASK=0b0):
        if STRING_OPTION in '-u': #Unlock nodes?
            temp = self.FBX_UNLOCK_MASK[self.FBX_OPTIONS[STRING_OPTION]]
            return QtCore.Qt.Checked if temp*BIT_MASK else QtCore.Qt.Unchecked
        return QtCore.Qt.Checked if self.FBX_OPTIONS[STRING_OPTION] == 'on' else QtCore.Qt.Unchecked

    def SetFBXCheckState(self, STRING_OPTION, CHECK_STATE, BIT_MASK=0b0):
        if STRING_OPTION in '-v':
            self.FBX_OPTIONS[STRING_OPTION] = 'float' if CHECK_STATE == QtCore.Qt.Checked else 'double'
        elif STRING_OPTION in '-u':
            temp = self.FBX_UNLOCK_MASK[self.FBX_OPTIONS[STRING_OPTION]]
            self.FBX_OPTIONS[STRING_OPTION]   = self.FBX_UNLOCK_MASK[temp ^ BIT_MASK]
        else:
            self.FBX_OPTIONS[STRING_OPTION] = 'on' if CHECK_STATE == QtCore.Qt.Checked else 'off'

    def GenerateCheckBox(self, STRING_NAME, STRING_FBX_OPTION, BIT_MASK=0b0):
        TEMP = QtGui.QCheckBox(STRING_NAME)
        TEMP.setCheckState(self.GetFBXCheckState(STRING_FBX_OPTION, BIT_MASK))

        if STRING_FBX_OPTION in '-u':
            TEMP.stateChanged.connect(lambda: self.SetFBXCheckState(STRING_FBX_OPTION, TEMP.checkState(), BIT_MASK))
        else:
            TEMP.stateChanged.connect(lambda: self.SetFBXCheckState(STRING_FBX_OPTION, TEMP.checkState()))
        return TEMP

    #####################
    #COMBO BOXES
    #####################
    def GenerateComboBox(self, STRING_FBX_OPTION, ITEMS=[]):
        TEMP = QtGui.QComboBox()
        TEMP.insertItems(0, ITEMS)
        TEMP.setCurrentIndex(self.GetComboBoxIndex(STRING_FBX_OPTION))
        TEMP.currentIndexChanged.connect(lambda: self.SetComboBoxIndex(STRING_FBX_OPTION, TEMP.currentIndex()))
        return TEMP

    def GetComboBoxIndex(self, STRING_OPTION):
        return 1 if self.FBX_OPTIONS[STRING_OPTION] == 'on' else 0

    def SetComboBoxIndex(self, STRING_FBX_OPTION, INDEX):
        if STRING_FBX_OPTION in '-s':
            self.FBX_OPTIONS[STRING_FBX_OPTION] = 'vex' if INDEX else 'vop'
        elif STRING_FBX_OPTION in '-a':
            self.FBX_OPTIONS[STRING_FBX_OPTION] = 'maya' if INDEX else 'off'
        elif STRING_FBX_OPTION in '-p':
            self.FBX_OPTIONS[STRING_FBX_OPTION] = 'abs' if INDEX else 'rel'
        else:
            self.FBX_OPTIONS[STRING_FBX_OPTION] = 'on' if INDEX else 'off'

    #####################
    #LINE EDITS
    #####################
    def GenerateLineEdit(self, STRING_FBX_OPTION):
        TEMP = QtGui.QLineEdit()
        TEMP.setText(self.GetLineEditText(STRING_FBX_OPTION))
        TEMP.textEdited.connect(lambda: self.SetLineEditText(STRING_FBX_OPTION, TEMP.text()))
        return TEMP

    def GetLineEditText(self, STRING_OPTION):
        return self.FBX_OPTIONS[STRING_OPTION]

    def SetLineEditText(self, STRING_OPTION, TEXT):
        self.FBX_OPTIONS[STRING_OPTION] = TEXT
        print self.FBX_OPTIONS[STRING_OPTION]

    #####################
    #GENERATE OPTIONS
    #####################
    def GenerateOptions(self):
        self.WIDGETS = []

        #DEFINE BASE/TEMP LAYOUTS
        WINDOW_WHOLE    =   QtGui.QVBoxLayout()

        #WIDGET CONSTRUCTION
        #####################
        #Top Line
        #####################
        WIDGET_FBX_EDIT = QtGui.QPushButton("Edit")
        self.WIDGETS.insert(self.AutoInsert(),
                    [QtGui.QLabel("File"),
                    self.WIDGET_FBX_INPUT,
                    WIDGET_FBX_EDIT,
                    QtGui.QPushButton("Help")]
                    )
        WIDGET_FBX_EDIT.clicked.connect(self.ShowWidgetsFileDialog)

        #####################
        #Filter Options
        #####################
        self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("Filter Options"))

        self.WIDGETS.insert(self.AutoInsert(),
                    [self.GenerateCheckBox("Cameras", '-c'),
                    self.GenerateCheckBox("Geometry", '-g'),
                    self.GenerateCheckBox("Animation", '-k')]
                    )

        self.WIDGETS.insert(self.AutoInsert(),
                    [self.GenerateCheckBox("Joints and Skin", '-j'),
                    self.GenerateCheckBox("Lights", '-l'),
                    self.GenerateCheckBox("Materials", '-s')]
                    )

        #####################
        #Animation Options
        #####################
        self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("Animation Options"))
#        ITEMS = ["TCB Curves Only", "All Cubic Curves"]
#        self.WIDGETS.insert(self.AutoInsert(),
#                    [QtGui.QLabel("Resample"),
#                    self.GenerateComboBox('-r', ITEMS),
#                    QtGui.QLabel("Every"),
#                    self.GenerateLineEdit('-q'),
#                    QtGui.QLabel("frames")]
#                    )

        self.WIDGETS.insert(self.AutoInsert(),
                    [self.GenerateCheckBox("Override FBX Frame Rate", '-f'),
                    self.GenerateLineEdit('-f'),
                    QtGui.QLabel("FPS")]
                    )

        #####################
        #Material Options
        #####################
        self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("Material Options"))

        ITEMS = ["FBX Shader Nodes", "VOP Networks"]
        self.WIDGETS.insert(self.AutoInsert(),
                    [QtGui.QLabel("Import Materials As: "),
                    self.GenerateComboBox('-s', ITEMS)]
                    )

        self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("Compatability Options"))

        ITEMS = ["FBX Standard", "Compatible with Maya"]
#        self.WIDGETS.insert(self.AutoInsert(),
#                    [QtGui.QLabel("Compatibility Mode: "),
#                    self.GenerateComboBox('-a', ITEMS)]
#                    )

        self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Treat All Vertex Caches as Single-Precision Types", '-v'))
        self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Triangulate NURBS and Patches", '-t'))
        #self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Import Blend Deformers as Blend SOPs", '-b'))

        #####################
        #General Options
        #####################
        self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("General Options"))
        ITEMS = ["Keep Absolute", "Convert to Relative"]
        self.WIDGETS.insert(self.AutoInsert(),
                    [QtGui.QLabel("File Paths: "),
                    self.GenerateComboBox('-p', ITEMS)]
                    )

        self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Unlock Geometry File SOPs (Requires Original FBX File)", '-u', 0b01))
        self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Unlock Deformation File CHOPs (Requires Original FBX File)", '-u', 0b10))
        #self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Hide Joints Attached to Skin", '-h'))
        #self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Import Null Nodes as Subnets", '-i'))
        self.WIDGETS.insert(self.AutoInsert(), self.GenerateCheckBox("Import Directly Into /obj Network", '-o'))

        #####################
        #Real-Time Options
        #####################
        # self.WIDGETS.insert(self.AutoInsert(), QtGui.QLabel("Real-Time Engine Options"))
        # self.WIDGETS.insert(self.AutoInsert(),
        #             [QtGui.QLabel("Compatibility"),
        #             QtGui.QComboBox()])
        # self.WIDGETS[self.INDEX-1][1].insertItems(0, ["Unreal Engine 4", "Unity 5"])

        #####################
        #Last Row Buttons!
        #####################
        WIDGET_Import   = QtGui.QPushButton("Import")
        WIDGET_Merge    = QtGui.QPushButton("Merge")
        WIDGET_Cancel   = QtGui.QPushButton("Cancel")
        self.WIDGETS.insert(self.AutoInsert(),
                    [WIDGET_Import,
                    WIDGET_Merge,
                    WIDGET_Cancel]
                    )
        WIDGET_Import.clicked.connect(self.ImportFBXNewScene)
        WIDGET_Merge.clicked.connect(self.ImportFBX)
        WIDGET_Cancel.clicked.connect(self.close)

        #CONSTRUCT ROW LAYOUTS AND ADD TO MAIN LAYOUT
        for index in range(0, len(self.WIDGETS)):
            WINDOW_WHOLE.addLayout(self.GenerateRowWidget(self.WIDGETS[index]))

        #CONSTRUCT CUSTOM LAYOUTS
        for index in range(0, len(self.CUSTOM_WIDGETS)):
           WINDOW_WHOLE.addLayout(self.GenerateRowWidget(self.CUSTOM_WIDGETS[index]))

        #SET LAYOUT
        self.setLayout(WINDOW_WHOLE)
