'''
Updated Fracture Rig tool designed to work with RealTimeVFXToolset.py.
'''

import hou
import RealTimeVFXToolset
# reload(RealTimeVFXToolset)

def init(nodes, frameRate=24):
    if checkSelections(nodes) == False:
        return "Tool failed! See above."

    geometryNodes = RealTimeVFXToolset.findNonDOPGeometry(nodes, 'soppath', 'dopobject')
    numberOfPieces = RealTimeVFXToolset.indexAttributeEntries(geometryNodes, 'name')

    rootNode = hou.node('/obj').createNode('subnet', 'FBX_RESULT')
    nodePieces = generateGeometry(geometryNodes, numberOfPieces, rootNode)
    modifyGeo(nodes, geometryNodes, nodePieces, numberOfPieces, rootNode)
    processMesh(nodes, nodePieces, numberOfPieces, frameRate)

def checkSelections(nodes):
    if RealTimeVFXToolset.nodeSelectionValid(nodes) == None: return False
    if RealTimeVFXToolset.nodeSelectionMatchType(nodes, 'rbdpackedobject') == None: return False
    if RealTimeVFXToolset.nodeSelectionMatchParm(nodes, 'soppath') == None: return False

def generateGeometry(geoNodes, numPieces, root):
    nodePieces = []

    for objectToProcess in range(0, len(geoNodes)):
        nodePieces.append([])

        for index in range(0, numPieces[objectToProcess]):
            tempName = geoNodes[objectToProcess].parent().name()

            if(hou.node(root.path() + tempName + "_PIECE" + str(index)) == None):
                nodePieces[objectToProcess].insert(index, root.createNode("geo", tempName + "_PIECE" + str(index)))
            else:
                nodePieces[objectToProcess].insert(index, hou.node(root.path() + tempName + "_PIECE" + str(index)))

        nodePieces[objectToProcess][0].parent().layoutChildren()

    return nodePieces

def modifyGeo(nodes, geometryNodes, nodePieces, numPieces, root):
    for objectToProcess in range(0, len(geometryNodes)):
        # refGeo = self.FindReferenceGeometry()
        refGeo = geometryNodes[objectToProcess]
        unpack = None
        deleteUnpack = None

        tempName = geometryNodes[objectToProcess].parent().name()

        if(refGeo.parent().node("UNPACK")  == None):
            unpack = refGeo.parent().createNode("unpack", "UNPACK")
        elif (refGeo.parent().node("UNPACK")  != None):
            unpack = refGeo.parent().node("UNPACK")
        else:
            print "ERROR 0: Cannot generate unpack node!"

        unpack.setFirstInput(refGeo)

        for index in range(0, numPieces[objectToProcess]):
            proxy   = None
            delete  = None
            xform   = None

            #################################
            #Create the nodes to process the
            #individual pieces
            #################################
            proxy = nodePieces[objectToProcess][index].createNode("object_merge", "PROXY")
            proxy.setParms({"objpath1":proxy.relativePathTo(unpack),
                            "xformtype":"object",
                            "xformpath":"../.."})

            delete = nodePieces[objectToProcess][index].createNode("delete", "DELETE")
            delete.setParms({'group':"@name=piece" + str(index),
                            'negate':'keep'})
            delete.setFirstInput(proxy)
            xform = nodePieces[objectToProcess][index].createNode("xform", "XFORM")


            #################################
            #This is important to grab the correct transform for the pieces.
            #Otherwise, all transforms will be at [0,0,0] and ruin your day.
            #The key here is finding the delta of the rest values between the
            #creation frame and the next frame.
            #################################
            xform.setFirstInput(delete)
            xform.parm('movecentroid').pressButton()

            creationFrame = nodes[objectToProcess].parm('createframe').eval()
            hou.setFrame(creationFrame)
            dopxform1 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
            hou.setFrame(creationFrame+1)
            dopxform2 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
            deltaXFORM = []
            hou.setFrame(creationFrame)

            for i in range(0,3):
                deltaXFORM.insert(i, dopxform1[i]-dopxform2[i])

            translates = [xform.parm('tx').eval(), xform.parm('ty').eval(), xform.parm('tz').eval()]
            result = [translates[0]+deltaXFORM[0], translates[1]+deltaXFORM[1], translates[2]+deltaXFORM[2]]
            result = []
            for i in range(0,3):
                result.insert(i, translates[i]+deltaXFORM[i])

            xform.setParms({'tx':result[0],
                            'ty':result[1],
                            'tz':result[2]})

            #################################
            #Delete original file node
            #################################
            if(str(hou.node(root.path() + "/" + tempName + "_PIECE" + str(index) + "/file1")) != "None"):
                hou.node(root.path() + "/" + tempName + "_PIECE" + str(index) + "/file1").destroy()
            hou.node(root.path() + "/" + tempName + "_PIECE" + str(index)).layoutChildren()

def processMesh(nodes, nodePieces, numPieces, frameRate=24):
    PARMS   =   ["tx", "ty", "tz", "rx", "ry", "rz", "px", "py", "pz"]
    RFSTART = int(hou.expandString('$RFSTART'))
    RFEND = int(hou.expandString('$RFEND'))

    for frame in range(RFSTART, RFEND+1, int(hou.fps()/frameRate)):
        hou.setFrame(frame)
        print "Processing Frame: " + str(frame)

        for objectToProcess in range(0, len(numPieces)):
            for index in range(0,numPieces[objectToProcess]):
                for index_parm in range(0,3):
                    hou_keyed_parm = nodePieces[objectToProcess][index].parm(PARMS[index_parm])
                    hou_keyframe = hou.Keyframe()
                    hou_keyframe.setFrame(frame)
                    hou_keyframe.setValue(nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('P')[index_parm])
                    hou_keyed_parm.setKeyframe(hou_keyframe)

                for index_parm in range(0,3):
                    hou_keyed_parm = nodePieces[objectToProcess][index].parm(PARMS[index_parm+3])
                    hou_keyframe = hou.Keyframe()
                    hou_keyframe.setFrame(frame)
                    hou_keyframe.setValue(hou.Quaternion(nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('orient')).extractEulerRotates()[index_parm])
                    hou_keyed_parm.setKeyframe(hou_keyframe)

    print "Processing Complete!"
