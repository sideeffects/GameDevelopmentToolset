"""


"""
import os
from collections import OrderedDict
from PySide import QtGui

HFS = os.getenv("HFS", "C:\Program Files\Side Effects Software\Houdini 15.5.500")

class Color(object):

    def __init__(self, name, value, is_preset=False):
        self.is_preset = is_preset
        self.name = name
        self.value = value

    def get_qcolor(self,_unusued = None):
        pass

    def get_formatted(self):
        pass


class AliasColor(Color):
    def get_qcolor(self, parser):
        if self.value not in parser.ordered_colors:
            return None

        alias_color = parser.ordered_colors[self.value]
        return alias_color.get_qcolor(parser)

class RGBColor(Color):

    def get_qcolor(self, _unusued = None):
        return QtGui.QColor.fromRgbF(self.value[0], self.value[1], self.value[2])

    def get_formatted(self):
        return ("%s \t \t%s\t%s\t%s\n")%(self.name, str(self.value[0]),str(self.value[1]),str(self.value[2]))

class HexColor(Color):
    def get_qcolor(self, _unusued = None):
        return QtGui.QColor(self.value)


class HSVColor(Color):
    def get_qcolor(self, _unusued = None):
        return QtGui.QColor.fromHsvF(self.value[0], self.value[1], self.value[2])


class ExpressionColor(Color):

    def get_qcolor(self, parser):
        function, value = self.value.split("(")
        value = value[:-1]

        rgb_color = parser.expressions[function](value)
        return QtGui.QColor.fromRgbF(rgb_color[0], rgb_color[1], rgb_color[2])


class HCSParser(object):

    def parse_preset_rgb_color(self, color_array):
        color_name = color_array[0]

        if color_array[1].startswith("#"):
            hex_color = color_array[1] + color_array[2] + color_array[3]
            self.ordered_colors[color_name] = HexColor(color_name, hex_color, is_preset=True)
            return

        rgb = map(float, color_array[1:])
        self.ordered_colors[color_name] = RGBColor(color_name, rgb, is_preset=True)

    def parse_preset_expression_color(self, color_array):
        color_name = color_array[0]
        color_function = color_array[1]

        self.ordered_colors[color_name] = ExpressionColor(color_name, color_function, is_preset=True)

    def parse_preset_expression(self, function_def):

        # TODO: just going to hardcode this for now, since there's only one
        if function_def[0] == "GREY(g)":
            self.expressions["GREY"] = lambda x: map(float, [x, x, x])

    def parse_preset_hsv_color(self, hsv_color_array):
        color_name = hsv_color_array[0]
        hsv_value = map(float, hsv_color_array[2:])

        hsv_value[0] /= 360

        self.ordered_colors[color_name] = HSVColor(color_name, hsv_value, is_preset = True)

    def parse_define_color_alias(self, color_alias):

        color_name = color_alias[1]
        alias_name = color_alias[2]

        self.ordered_colors[color_name] = AliasColor(color_name, alias_name, is_preset=True)

    def parse_include_line(self, line):
        include_path = line.split()[-1].replace("$HFS", HFS).replace("\"", "")
        include_parser = HCSParser(include_path)

        self.expressions.update(include_parser.expressions)
        self.ordered_colors.update(include_parser.ordered_colors)

    def parse_define_line(self, line):
        split_line = line.split()

        # function
        if "(" in split_line[1]:
            self.parse_preset_expression(split_line[1:])
            return

        if len(split_line) == 5:
            self.parse_preset_rgb_color(split_line[1:])
            return

        if len(split_line) == 6 and split_line[2] == "HSV":
            self.parse_preset_hsv_color(split_line[1:])
            return

        if "(" in split_line[2]:
            self.parse_preset_expression_color(split_line[1:])
            return

        self.parse_define_color_alias(split_line)

    def parse_ui_rgb_color(self, rgb_color):
        color_name = rgb_color[0]
        if rgb_color[1].startswith("#"):
            hex_value = rgb_color[1] + rgb_color[2] + rgb_color[3]
            self.ordered_colors[color_name] = HexColor(color_name, hex_value)
            return

        rgb_value = map(float, rgb_color[1:])
        self.ordered_colors[color_name] = RGBColor(color_name, rgb_value)

    def parse_ui_hsv_color(self, hsv_color):
        color_name = hsv_color[0]

        hsv_value = map(float, hsv_color[2:])
        hsv_value[0] /= 360

        self.ordered_colors[color_name] = HSVColor(color_name, hsv_value)

    def parse_ui_function_color(self, color_function):
        color_name = color_function[0]
        function_value = color_function[1]

        self.ordered_colors[color_name] = ExpressionColor(color_name, function_value)

    def parse_ui_alias_color(self, color_alias):
        color_name = color_alias[0]
        alias_name = color_alias[1]

        self.ordered_colors[color_name] = AliasColor(color_name, alias_name)

    def parse_ui_color_line(self, color_line):
        if len(color_line) == 4:
            self.parse_ui_rgb_color(color_line)
            return

        if len(color_line) >= 5 and color_line[1].upper() == "HSV":
            self.parse_ui_hsv_color(color_line)
            return

        if "(" in color_line[1]:
            self.parse_ui_function_color(color_line)
            return

        try:
            val = float(color_line[1])
            # THIS IS FOR SCALARS THAT I'M IGNORING FOR NOW
            return
        except ValueError:
            pass

        self.parse_ui_alias_color(color_line)

        # print color_line
    def __init__(self, hcs_file):

        self.expressions = {}
        self.ordered_colors = OrderedDict()
        self.modified_colors = {}

        self.hcs_file = hcs_file
        self.parse()

    def parse(self):
        with open(self.hcs_file, 'r') as f:
            for line in f.readlines():
                line = line.strip() # remove whitespaces

                # skip blank lines
                if not line:
                    continue

                # skip comments
                if line.startswith("//"):
                    continue

                if line.startswith("Scheme:"): # ignore scheme names
                    continue
                    
                line = line.split("//")[0]  # remove trailing comments

                if line.startswith("#include"):
                    self.parse_include_line(line)
                    continue

                if line.startswith("#define"):
                    self.parse_define_line(line)
                    continue

                split_line = line.split()
                if len(split_line) >= 2:
                    self.parse_ui_color_line(split_line)
                    continue

                print "Failed to match:", line

    def save(self, filename=None):
        if not filename:
            filename = self.hcs_file

        new_file_data = []
        with open(self.hcs_file, 'r') as f:
            for line in f.readlines():
                if not line.strip() or line.startswith("//") or line.startswith("Scheme:"):
                    new_file_data.append(line)
                    continue

                match = 0
                for modified_color in self.modified_colors:
                    if self.modified_colors[modified_color].is_preset:
                        pass
                    else:

                        split_line = line.split()
                        if not len(split_line):
                            continue

                        if split_line[0] == modified_color:
                            match = 1
                            color = self.modified_colors[modified_color]
                            new_line = color.get_formatted()

                            new_file_data.append(new_line)

                if not match:
                    new_file_data.append(line)

        with open(filename, 'w') as f:
            f.writelines(new_file_data)

        self.modified_colors = {}
