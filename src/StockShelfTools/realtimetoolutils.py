import hou
import os

'''Real Time Tool Utilities
These utilities are designed as helpers for the real-time vfx shelf tools. You
can find things such as flipbook rig generator and other tools.
'''

def createProjectFolder(folder):
    '''
    Create new folder within the project folder. It'll automatically evaluate
    $HIP and append the first '/'. Start the parameter immediately with a folder

    ex. "render", "sims", "renders/set1", "sims/set1"
    '''
    hipFolder = hou.expandString("$HIP")

    if not os.path.exists(hipFolder + "/" + folder):
        os.makedirs(hipFolder + "/" + folder)
