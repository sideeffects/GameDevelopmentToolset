import hou
from PySide import QtCore
from PySide import QtGui
import FractureRig

class FractureRigUI(QtGui.QWidget):
    WINDOW_LAYOUT   = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    CSS             = hou.expandString('$HOUDINI_USER_PREF_DIR')
    WIDGETS         = []
    frameRate       = 24

    def __init__(self, parent=None):
        app = QtGui.QWidget.__init__(self, parent)
        self.generateWindow()

    def setFrameRate(self, frameRate):
        self.frameRate = frameRate

    #DELETE
    def generateRowWidget(self, WidgetArray):
        ROW = QtGui.QHBoxLayout()

        if isinstance(WidgetArray, list):
            for index in range(0,len(WidgetArray)):
                ROW.addWidget(WidgetArray[index])
        else:
            ROW.addWidget(WidgetArray)

        return ROW

    def generateWindow(self):
        self.setWindowTitle("Fracture Rig Options")
        self.setGeometry(1024, 512, 400, 512)

        CSS_FILE = QtCore.QFile(self.CSS)
        CSS_FILE.open(QtCore.QFile.ReadOnly)
        CSS_RESULT = CSS_FILE.readAll()
        self.setStyleSheet(CSS_RESULT.data())

        self.generateOptions()

    def generateOptions(self):
        self.WIDGETS = []

        WINDOW_WHOLE = QtGui.QVBoxLayout()

        WIDGET_FPSLabel = QtGui.QLabel("Frame Rate of Destruction")
        self.WIDGETS.append(WIDGET_FPSLabel)

        WIDGET_FRAMERATE = QtGui.QLineEdit()
        WIDGET_FRAMERATE.setText('24')
        WIDGET_FRAMERATE.textEdited.connect(lambda: self.setFrameRate(WIDGET_FRAMERATE.text()))
        self.WIDGETS.append(WIDGET_FRAMERATE)

        WIDGET_CANCEL = QtGui.QPushButton("Cancel")
        WIDGET_CANCEL.clicked.connect(self.close)
        self.WIDGETS.append(WIDGET_CANCEL)

        WIDGET_ACCEPT = QtGui.QPushButton("Accept")
        WIDGET_ACCEPT.clicked.connect(self.processMesh)
        self.WIDGETS.append(WIDGET_ACCEPT)

        for widget in self.WIDGETS:
            WINDOW_WHOLE.addLayout(self.generateRowWidget(widget))

        self.setLayout(WINDOW_WHOLE)

    def processMesh(self):
        FractureRig.init(hou.selectedNodes(), int(self.frameRate))
