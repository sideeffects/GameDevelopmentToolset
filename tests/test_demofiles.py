
import os
import hou

import unittest
local_dir = os.path.dirname(__file__)

class TestStringMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def test_1_test_demoscenes(self):

        demo_files = os.listdir("../hip")
        for demo_file in demo_files:
            if demo_file.endswith(".hip"):
                print "opening", demo_file
                try:
                    hou.hipFile.load(os.path.join("..", "hip", demo_file).replace("\\", "/"))
                except Exception, e:
                    print str(e)
                    pass


if __name__ == '__main__':
    unittest.main()