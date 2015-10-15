'''
Prefractured Mesh Prep
Author: Steven Burrichter
Company: Side Effects Software
Last Updated: 10/1/2015
Reference Build: H15.0.252
'''

import hou

class PREFRACTURE_EXPORT:
    ######################################
    #VARIABLES
    ######################################
    node            =   None
    numberOfPieces  =   0

    nodeSubnet      =   None
    nodePieces      =   []
    nodeDisplay     =   None
    PARMS           =   ["tx", "ty", "tz", "rx", "ry", "rz", "px", "py", "pz"]

    ######################################
    #FUNCTIONS
    ######################################

    #################################
    #Did the user actually grab the
    #correct node?
    #################################
    def CheckObject(self):
        self.node = hou.selectedNodes()

        if len(self.node) > 1:
            return False
        elif len(self.node) < 1:
            return False
        else:
            node_type = self.node[0].type()

        #Check sop node for "pieces" prim name attribute?
        if self.node[0].geometry().findPrimAttrib("name"):
            if self.node[0].geometry().findPrimAttrib("name").strings()[0].startswith("piece"):
                return True
            else:
                print "String must contain 'piece'."
                return False
        else:
            print "No name attribute found!"
            return False

    #################################
    #Grabs the initial data
    #################################
    def GrabPieces(self):
        self.node = self.node[0]
        # self.nodeDisplay = self.FindReferenceGeometry()
        obj_geometry = self.node.geometry()

        if obj_geometry.findPointAttrib("name") == None:
            list_pieces = obj_geometry.findPrimAttrib("name").strings()
        else:
            list_pieces = obj_geometry.findPointAttrib("name").strings()

        self.numberOfPieces = len(list_pieces)

    #################################
    #Creates the subnet to contain
    #the animated pieces
    #################################
    def GenerateRoot(self):
        if(hou.node("/obj/FBX_RESULT") == None):
            self.nodeSubnet = hou.node("/obj").createNode("subnet", "FBX_RESULT")
        else:
            self.nodeSubnet = hou.node("/obj/FBX_RESULT")

    #################################
    #Creates the initial geo nodes
    #for the pieces
    #################################
    def GenerateGeo(self):
        for index in range(0, self.numberOfPieces):
            if(hou.node("/obj/FBX_RESULT/PIECE" + str(index)) == None):
                self.nodePieces.insert(index, self.nodeSubnet.createNode("geo", "PIECE" + str(index)))
            else:
                self.nodePieces.insert(index, hou.node("/obj/FBX_RESULT/PIECE" + str(index)))

    #################################
    #Modifies the created piece geo
    #nodes. A few nodes are added
    #with custom expressions.
    #################################
    def ModifyGeo(self):
        for index in range(0, self.numberOfPieces):
            proxy   = None

            #################################
            #Create the nodes to process the
            #individual pieces
            #################################
            if(hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/PROXY")  == None):
                proxy = self.nodePieces[index].createNode("object_merge", "PROXY")
            elif (hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/PROXY")  != None):
                proxy = hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/PROXY")
            else:
                print "ERROR 0: Cannot generate proxy node!"

            proxy.setParms({"objpath1":proxy.relativePathTo(self.node),
                            "group1":"@name=piece{}".format(index),
                            "xformtype":"object",
                            "xformpath":"../.."})

            #################################
            #Delete original file node
            #################################
            if(str(hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/file1")) != "None"):
                hou.node("/obj/FBX_RESULT/PIECE" + str(index) + "/file1").destroy()

        self.ArrangeAllNodes("/obj/FBX_RESULT")

    #################################
    #Just to set the layouts
    #################################
    def ArrangeAllNodes(self, path):
        hou.node(path).layoutChildren()

    ######################################
    #MAIN
    ######################################
    def __init__(self):
        if self.CheckObject():
            # print "Object Valid"
            self.GrabPieces()
            self.GenerateRoot()
            self.GenerateGeo()
            self.ModifyGeo()
        else:
            print "Error! See above."
