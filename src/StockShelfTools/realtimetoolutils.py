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

def sliceSourceObject(objNode):
    '''
    Creates the required network to slice a mesh.
    TODO: Set alignment.
    0=xy
    1=xz
    2=yz
    '''
    toCollapse = []
    displayNode = objNode.displayNode()
    temp1 = displayNode.createOutputNode('convert', "convertMesh")
    temp1.setParms({'lodu':5,
                    'lodv':5})
    toCollapse.append(temp1)

    temp2 = temp1.createOutputNode('attribpromote', "getMaxPos")
    temp2.setParms({'inname':'P',
                    'outclass':0, #to detail
                    'method':0, #Get max
                    'useoutname':True,
                    'outname':"posMax"})
    toCollapse.append(temp2)

    temp3 = temp2.createOutputNode('attribpromote', "getMinPos")
    temp3.setParms({'inname':'P',
                    'outclass':0, #to detail
                    'method':1, #Get min
                    'useoutname':True,
                    'outname':"posMin"})
    toCollapse.append(temp3)

    temp4 = temp3.createOutputNode('cookie', "createSlice")
    temp4.setParms({'boolop':'intersect',
                    'closedA':True,
                    'closedB':True})
    temp4.setDisplayFlag(True)
    temp4.setRenderFlag(True)
    toCollapse.append(temp4)

    temp5 = temp4.createInputNode(1, 'grid', "slicingObject")
    temp5.setParms({'orient':'xy',
                    'sizex':temp4.geometry().attribValue("posMax")[0]-temp4.geometry().attribValue("posMin")[0]+1,
                    'sizey':temp4.geometry().attribValue("posMax")[1]-temp4.geometry().attribValue("posMin")[1]+1,
                    'rows':500,
                    'cols':500})
    toCollapse.append(temp5)

    objNode.collapseIntoSubnet(toCollapse, "sliceMesh")
