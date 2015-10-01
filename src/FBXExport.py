import hou
from PySide import QtCore
from PySide import QtGui
import FBXExportUI
reload(FBXExportUI)
from FBXExportUI import CustomUI

class CustomExport(QtGui.QWidget):
    CSS         = hou.expandString('$HOUDINI_USER_PREF_DIR') + "/toolbar/src/RealTimeVFX.qss"
    FBX_FILE    = hou.expandString('$HIP')
    WIDGETS     = []
    PARMS       = ({'trange':'off',
                    'f1':1,
                    'f2':240,
                    'f3':1,
                    'take':'_current',
                    'sopoutput':'$HIP/out.fbx',
                    'mkpath':'on',
                    'startnode':'/obj',
                    'exportkind':'on',
                    'sdkversion':'FBX | FBX201400',
                    'vcformat':'mayaformat',
                    'invisobj':'nullnodes',
                    'polylod':'1',
                    'detectconstpointobjs':'on',
                    'convertsurfaces':'off',
                    'conservemem':'off',
                    'deformsasvcs':'off'})

    PARM_OPTIONS    = ({'Render Current Frame':'off',
                        'Render Frame Range':'normal'
                        'Render Frame Range Only (Strict)':'on',
                        '(Current)':'_current_'
                        'Main':'Main',
                        'FBX | FBX201400':'FBX | FBX201400',
                        'FBX | FBX201300':'FBX | FBX201300',
                        'FBX | FBX201200':'FBX | FBX201200',
                        'FBX | FBX201100':'FBX | FBX201100',
                        'FBX 6.0 | FBX201000':'FBX 6.0 | FBX201000',
                        'FBX 6.0 | FBX200611':'FBX 6.0 | FBX200611',
                        'Maya Compatible (MC)':'mayaformat',
                        '3DS MAX Compatible (PC2)':'maxformat',
                        'As Hidden Null Nodes':'nullnodes',
                        'As Hidden Full Nodes':'fullnodes'
                        })

    def __init__(self, parent=None):
        app = QtGui.QWidget.__init__(self, parent)

        self.GenerateWindow()

    def GenerateWindow(self):
        self.setWindowTitle("Custom FBX Export")
        self.setGeometry(1024, 512, 400, 512)

        CSS_FILE = QtCore.QFile(self.CSS)
        CSS_FILE.open(QtCore.QFile.ReadOnly)
        CSS_RESULT = CSS_FILE.readAll()
        self.setStyleSheet(CSS_RESULT.data())

        self.GenerateOptions()

    def GenerateOptions(self):
        self.WIDGETS = []

        WINDOW_WHOLE = QtGui.QVBoxLayout()

        #####################
        #Top Line
        #####################
        WIDGET_FBX_EDIT = QtGui.QPushButton
