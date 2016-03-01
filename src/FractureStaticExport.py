'''
This tool is designed to take a series of packed objects at the SOP level,
unpack them, separate them into a separate subnet with their own geo nodes,
and keyframe their animations according to the timeline.
'''

import hou
import RealTimeVFXToolset
reload(RealTimeVFXToolset)

def init(nodes):
    # if RealTimeVFXToolset.nodeSelectionMatchType(nodes, 'assemble') == False:
    #     return 'Error! See above.'

    numberOfPieces = RealTimeVFXToolset.indexAttributeEntries(nodes, 'name')
    rootNode = hou.node('/obj').createNode('subnet', 'FBX_RESULT')

    nodePieces = generateGeometry(nodes, numberOfPieces, rootNode)
    modifyGeo(nodes, nodePieces, numberOfPieces, rootNode)
    print 'Success'

def generateGeometry(nodes, numPieces, root):
    nodePieces = []

    for objectToProcess in range(0, len(nodes)):
        nodePieces.append([])

        for index in range(0, numPieces[objectToProcess]):
            tempName = nodes[objectToProcess].name()

            if(hou.node('{}{}_PIECE{}'.format(root.path(), tempName, index)) == None):
                nodePieces[objectToProcess].insert(index, root.createNode('geo', '{}_PIECE{}'.format(tempName, index)))
            else:
                nodePieces[objectToProcess].insert(index, hou.node('{}{}_PIECE{}'.format(root.path(), tempName, index)))

            nodePieces[objectToProcess][0].parent().layoutChildren()

    return nodePieces

def modifyGeo(nodes, nodePieces, numPieces, root):
    for objectToProcess in range(0, len(nodes)):
        refGeo = nodes[objectToProcess]
        unpack = None
        deleteUnpack = None

        tempName = nodes[objectToProcess].name()

        if(refGeo.parent().node('UNPACK{}'.format(objectToProcess))  == None):
            unpack = refGeo.parent().createNode("unpack", 'UNPACK{}'.format(objectToProcess))
        elif (refGeo.parent().node('UNPACK{}'.format(objectToProcess))  != None):
            unpack = refGeo.parent().node('UNPACK{}'.format(objectToProcess))
        else:
            print "ERROR 0: Cannot generate unpack node!"

        unpack.setFirstInput(refGeo)

        #Locks the unpack node to prevent processing during FBX Export
        if(unpack.isLocked()):
            unpack.setHardLocked(False)
            unpack.setHardLocked(True)
        else:
            unpack.setHardLocked(True)

        for index in range(0, numPieces[objectToProcess]):
            proxy   = None
            delete  = None

            proxy = nodePieces[objectToProcess][index].createNode("object_merge", "PROXY")
            proxy.setParms({"objpath1":proxy.relativePathTo(unpack),
                            "xformtype":"object",
                            "xformpath":"../.."})

            delete = nodePieces[objectToProcess][index].createNode("delete", "DELETE")
            delete.setParms({'group':"@name=piece{}".format(index),
                            'negate':'keep'})
            delete.setFirstInput(proxy)

            #################################
            #Delete original file node
            #################################
            if(delete.parent().node('file1') != None):
                delete.parent().node("file1").destroy()
            delete.parent().layoutChildren()

def processMesh(nodes, nodePieces, numPieces):
    PARMS   =   ["tx", "ty", "tz", "rx", "ry", "rz", "px", "py", "pz"]
    RFSTART = int(hou.expandString('$RFSTART'))
    RFEND = int(hou.expandString('$RFEND'))

    initialParmData = []

    #GET INITIAL TRANSFORMS
    hou.setFrame(frame)
    for objectToProcess in range(0, len(numPieces)):
        initialParmData.append(objectToProcess)

        for index in range(0, numPieces[objectToProcess]):
            initialParmData[objectToProcess].append(index)

            for index_parm in range(0,3):
                #Get original tx,ty,tz
                initialParmData[objectToProcess][index].append(nodes[objectToProcess].points()[index].attribValue('P')[index_parm])

            for index_parm in range(0,3):
                #Get original rx,ry,rz
                initialParmData[objectToProcess][index].append(nodes[objectToProcess].points()[index].attribValue('R')[index_parm])
