import hou
from PySide import QtCore
from PySide import QtGui
import RealTimeVFXToolset

class KeyframeRemover(QtGui.QWidget):
    WINDOW_LAYOUT   = QtGui.QBoxLayout(QtGui.QBoxLayout.TopToBottom)
    CSS             = hou.expandString('$HOUDINI_USER_PREF_DIR')
    WIDGETS         = []

    startFrame  = 1
    endFrame    = 240
    step        = 1
    parameters = ["tx", "ty", "tz", "rx", "ry", "rz"]

    def __init__(self, parent=None):
        app = QtGui.QWidget.__init__(self, parent)
        self.generateWindow()

    def setStartFrame(self, input):
        self.startFrame = input

    def setEndFrame(self, input):
        self.endFrame = input

    def setStep(self, input):
        self.step = input

    def generateRowWidget(self, WidgetArray):
        ROW = QtGui.QHBoxLayout()

        if isinstance(WidgetArray, list):
            for index in range(0,len(WidgetArray)):
                ROW.addWidget(WidgetArray[index])
        else:
            ROW.addWidget(WidgetArray)

        return ROW

    def generateWindow(self):
        self.setWindowTitle("Keyframe Remover Options")
        self.setGeometry(1024, 512, 400, 512)

        CSS_FILE = QtCore.QFile(self.CSS)
        CSS_FILE.open(QtCore.QFile.ReadOnly)
        CSS_RESULT = CSS_FILE.readAll()
        self.setStyleSheet(CSS_RESULT.data())

        self.generateOptions()

    def generateOptions(self):
        self.WIDGETS = []

        WINDOW_WHOLE = QtGui.QVBoxLayout()

        WIDGET_FRAMETEXT = QtGui.QLabel("Frame Start/Frame End/Step")
        self.WIDGETS.append(WIDGET_FRAMETEXT)

        WIDGET_START = QtGui.QLineEdit()
        WIDGET_START.setText('1')
        WIDGET_START.textEdited.connect(lambda: self.setStartFrame(WIDGET_START.text()))

        WIDGET_END = QtGui.QLineEdit()
        WIDGET_END.setText('240')
        WIDGET_END.textEdited.connect(lambda: self.setEndFrame(WIDGET_END.text()))

        WIDGET_STEP = QtGui.QLineEdit()
        WIDGET_STEP.setText('1')
        WIDGET_STEP.textEdited.connect(lambda: self.setStep(WIDGET_STEP.text()))

        self.WIDGETS.append([WIDGET_START, WIDGET_END, WIDGET_STEP])

        WIDGET_CANCEL = QtGui.QPushButton("Cancel")
        WIDGET_CANCEL.clicked.connect(self.close)

        WIDGET_ACCEPT = QtGui.QPushButton("Accept")
        WIDGET_ACCEPT.clicked.connect(self.processMesh)

        self.WIDGETS.append([WIDGET_CANCEL, WIDGET_ACCEPT])

        for widget in self.WIDGETS:
            WINDOW_WHOLE.addLayout(self.generateRowWidget(widget))

        self.setLayout(WINDOW_WHOLE)

    def processMesh(self):
        RealTimeVFXToolset.deleteKeyframes(hou.selectedNodes(), int(self.startFrame), int(self.endFrame), int(self.step), self.parameters)
