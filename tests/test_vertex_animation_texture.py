import hou
import os

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_frame_0_bug(self):
        hou.hipFile.load(os.path.join(local_dir, "hip", "vertex_animation_texture_0_frame_bug.hip").replace("\\", "/"))
        node = hou.node("/out/vertex_animation_textures1")
        node.render()

   # @classmethod
    #def tearDownClass(cls):
       #os.remove(os.path.join(local_dir, "hip", "export.csv"))

if __name__ == '__main__':
    unittest.main()