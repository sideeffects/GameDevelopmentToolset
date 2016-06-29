"""
    TODO Launch with the colors set


"""
from PySide import QtGui, QtCore
from parse_hcs import HCSParser, RGBColor
from functools import partial
import sys
import os

if "houdini" in sys.executable:
    import hou


class ColorManagerWidget(QtGui.QWidget):

    def __init__(self, parent=None, preset_file=None):
        super(ColorManagerWidget, self).__init__(parent)
        self.setBaseSize(QtCore.QSize(800,800))

        self.get_hcs_files()

        # Container Widget
        central_widget = QtGui.QWidget()
        self.central_layout = QtGui.QVBoxLayout(central_widget)

        self.build_color_preset_grp()

        tab_group = QtGui.QTabWidget()

        self.preset_tab = QtGui.QWidget()
        self.color_tab = QtGui.QWidget()

        QtGui.QVBoxLayout(self.color_tab)
        QtGui.QVBoxLayout(self.preset_tab)

        tab_group.addTab(self.color_tab, "Colors")
        tab_group.addTab(self.preset_tab, "Presets")

        self.central_layout.addWidget(tab_group)

        self.preset_file = preset_file

        if self.preset_file:
            self.parser = HCSParser(HCS_File)
            self.refresh_tabs()
        else:
            self.set_hcs_file(self.hcs_files[0])

        # Scroll Area Properties
        scroll = QtGui.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central_widget)

        # Scroll Area Layer add
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(scroll)

        self.setLayout(vLayout)


    def get_hcs_files(self):
        user_pref = os.path.join(os.environ["HOUDINI_USER_PREF_DIR"], "config")
        HFS = os.path.join(os.environ["HFS"], "houdini", "config")

        self.hcs_files = []
        search_dirs = [user_pref, HFS]
        for search_dir in search_dirs:
            for filename in os.listdir(search_dir):
                if filename.endswith(".hcs"):
                    self.hcs_files.append(os.path.join(search_dir, filename))


    def refresh_tabs(self):
        clearLayout(self.preset_tab.layout())

        self.build_color_tab(self.preset_tab, preset=True)
        self.build_color_tab(self.color_tab, preset=False)

    def build_color_tab(self, parent_tab, preset=False):
        color_layout = parent_tab.layout()

        for color_name in self.parser.ordered_colors.keys():

            color = self.parser.ordered_colors[color_name]
            if color.is_preset != preset:
                continue

            color_item_layout = QtGui.QHBoxLayout()

            color_lbl = QtGui.QLabel(color_name)
            color_item_layout.addWidget(color_lbl)

            color_btn = QtGui.QPushButton()
            color_btn.setStyleSheet("background-color: %s;" % "pink")

            q_color = self.parser.ordered_colors[color_name].get_qcolor(self.parser)
            if q_color:
                color_btn.setStyleSheet("background-color: %s;" % q_color.name())
            else:
                print "COLOR FAILED ", color_name, self.parser.ordered_colors[color_name].value

            color_btn.clicked.connect(partial(self.on_btn, color_name, color_btn))
            color_item_layout.addWidget(color_btn)
            color_layout.addLayout(color_item_layout)

        color_layout.addStretch()
        # parent_tab.setLayout(color_layout)

    def on_btn(self, color_name, color_btn):

        color  = QtGui.QColorDialog().getColor()
        if color.isValid():
            color_btn.setStyleSheet("background-color: %s;" % color.name())
            self.parser.modified_colors[color_name] = RGBColor(color_name, [color.redF(), color.greenF(), color.blueF()])
            self.parser.save()
            if "houdini" in sys.executable:
                hou.ui.reloadViewportColorSchemes()

    def set_hcs_file(self, hcs_file):
        self.hcs_file = hcs_file
        self.parser = HCSParser(self.hcs_file)
        self.refresh_tabs()

    def preset_changed(self, itemIndex):
        print itemIndex
        self.set_hcs_file(self.hcs_files[itemIndex])

    def build_color_preset_grp(self):
        preset_name_grp = QtGui.QGroupBox("Color Scheme")

        preset_layout = QtGui.QHBoxLayout(preset_name_grp)

        name_lbl = QtGui.QLabel("Preset_Name")
        preset_combo = QtGui.QComboBox()

        for hcs_file in self.hcs_files:
            root, filename = os.path.split(hcs_file)
            preset_combo.addItem(filename)

        preset_combo.currentIndexChanged.connect(self.preset_changed)

        preset_combo.setMinimumWidth(300)

        duplicate_btn = QtGui.QPushButton("Duplicate")
        delete_btn = QtGui.QPushButton("Delete")

        preset_layout.addWidget(name_lbl)
        preset_layout.addWidget(preset_combo)
        preset_layout.addWidget(duplicate_btn)
        preset_layout.addWidget(delete_btn)

        self.central_layout.addWidget(preset_name_grp)

def clearLayout(layout):
    if not layout:
        return

    while layout.count():
        child = layout.takeAt(0)
        print child
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clearLayout(child.layout())
        elif child.spacerItem() is not None:
            del(child)

if __name__ == '__main__':

    app = QtGui.QApplication([])

    # Create top level window/button
    button = ColorManagerWidget()
    # Call function that invokes color selection dialog when the button is clicked
    # button.clicked.connect(choose_color)
    button.show()

    app.exec_()