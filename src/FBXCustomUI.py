from PySide import QtGui
'''
CUSTOM_WIDGETS is each row
Lists inside of CUSTOM_WIDGETS creates columns
Currently new UI is added to the bottom of the Window
Looking into tabs for possible development
'''
def CustomUI():
    CUSTOM_WIDGETS = []
    CUSTOM_WIDGETS.insert(0, QtGui.QLabel("Post Script Options"))
    CUSTOM_WIDGETS.insert(1, [QtGui.QLabel("Compatibility"),
                    QtGui.QComboBox()])
    CUSTOM_WIDGETS[1][1].insertItems(0, ["Frostbite", "Unreal Engine 4",
                                "Maya"])

    return CUSTOM_WIDGETS
