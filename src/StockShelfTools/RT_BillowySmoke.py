import hou

class BillowySmoke():
    sourceNode = None

    def __init__(self, parent=None):
        self.CommandStack()

    def CommandStack(self):
        if self.CheckForSource():
            print self.sourceNode
            self.PrepFuelSource()
        else:
            print "Error! See Above."

    def CheckForSource(self):
        self.sourceNode = hou.selectedNodes()

        if len(self.sourceNode) > 1:
            return False
        elif len(self.sourceNode) < 1:
            return False
        else:
            self.sourceNode = self.sourceNode[0]
            return True

    def PrepFuelSource(self):
        self.CreateNodeInline("fluidsource", "create_density_volume", self.sourceNode.displayNode(), True, False)
        self.CreateNodeInline("merge", "merge_density_volumes", self.sourceNode.displayNode(), True, False)
        self.CreateNodeInline("null", "OUT_density", self.sourceNode.displayNode(), True, False)
        self.CreateNodeInline("null", "RENDER", self.sourceNode.displayNode(), False, True, False)
        self.sourceNode.layoutChildren()
        # self.sourceNode.createNode("fluidsource", "create_density_volume").setFirstInput(self.sourceNode.displayNode()).setDisplayFlag(True)
        # self.sourceNode.createNode("merge", "merge_density_volumes").setFirstInput(self.sourceNode.displayNode()).setDisplayFlag(True)
        # self.sourceNode.createNode("null", "OUT_density").setFirstInput(self.sourceNode.displayNode()).setDisplayFlag(True)
        # self.sourceNode.createNode("null", "RENDER").setRenderFlag(True)

    '''FUNC: CreateNodeInline
    nodeType: Type of node ("null", "merge")
    nodeName: Label of node ("AwesomeNull", "NeatSim")
    referenceNode: Reference SopNode to build off of. Still reference one even if not connecting.
    setDisplayFlag: Set the display flag (True/False)
    setRenderFlag: Set the render flag (True/False)
    connectToInput: Determines if node connects or is isolated
    '''
    def CreateNodeInline(self, nodeType="null", nodeName="null", referenceNode=None, setDisplayFlag=True, setRenderFlag=True, connectToInput=True):
        temp = referenceNode.parent().createNode(nodeType, nodeName)
        if connectToInput:
            temp.setFirstInput(referenceNode.parent().displayNode())
        temp.setDisplayFlag(setDisplayFlag)
        temp.setRenderFlag(setRenderFlag)
