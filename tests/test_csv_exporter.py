import hou
import os

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_loadfile(self):
        hou.hipFile.load(os.path.join(local_dir, "hip", "csv_editor.hip").replace("\\", "/"))

    def test_2_checkfoo(self):
        assert(len(hou.node("/out").children()) == 1)

    def test_3_checkfoo(self):
        node = hou.node("/out/rop_csv_exporter1")
        node.render()
        assert(os.path.exists(os.path.join(local_dir, "hip", "export.csv")))

    @classmethod
    def tearDownClass(cls):
       os.remove(os.path.join(local_dir, "hip", "export.csv"))

if __name__ == '__main__':
    unittest.main()