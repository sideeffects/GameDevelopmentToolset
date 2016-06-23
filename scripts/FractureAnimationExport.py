'''
Updated Fracture Rig tool designed to work with RealTimeVFXToolset.py.
Takes a Packed Rigid Body DOP, splits the individual pieces out, and keyframes their transforms.
'''

import hou

import RealTimeVFXToolset

reload(RealTimeVFXToolset)

def init(nodes):
    if checkSelections(nodes) == False:
        return 'Tool failed! See above.'

    geometryNodes = RealTimeVFXToolset.findNonDOPGeometry(nodes, 'soppath', 'dopobject')
    numberOfPieces = RealTimeVFXToolset.indexAttributeEntries(geometryNodes, 'name')

    if checkNaming(geometryNodes) == False:
        return 'Tool failed! See above.'

    rootNode = hou.node('/obj').createNode('subnet', 'FBX_RESULT')
    nodePieces = generateGeometry(geometryNodes, numberOfPieces, rootNode)
    modifyGeo(nodes, geometryNodes, nodePieces, numberOfPieces, rootNode)
    processMesh(nodes, nodePieces, numberOfPieces)

    for nodes in nodePieces:
        RealTimeVFXToolset.keyframeReducer(nodes, ['tx', 'ty', 'tz',
                                                    'rx', 'ry', 'rz'])

def checkSelections(nodes):
    if RealTimeVFXToolset.nodeSelectionValid(nodes) == None: return False
    if RealTimeVFXToolset.nodeSelectionMatchType(nodes, 'rbdpackedobject') == None: return False
    if RealTimeVFXToolset.nodeSelectionMatchParm(nodes, 'soppath') == None: return False

def checkNaming(nodes):
    if RealTimeVFXToolset.checkPointAttributeNaming(nodes, 'name') == None: return False

def generateGeometry(geoNodes, numPieces, root):
    nodePieces = []

    for objectToProcess in range(0, len(geoNodes)):
        nodePieces.append([])

        for index in range(0, numPieces[objectToProcess]):
            tempName = geoNodes[objectToProcess].parent().name()

            if(hou.node('{}{}_PIECE{}'.format(root.path(), tempName, index)) == None):
                nodePieces[objectToProcess].insert(index, root.createNode('geo', '{}_PIECE{}'.format(tempName, index)))
            else:
                nodePieces[objectToProcess].insert(index, hou.node('{}{}_PIECE{}'.format(root.path(), tempName, index)))

        nodePieces[objectToProcess][0].parent().layoutChildren()

    return nodePieces

def modifyGeo(nodes, geometryNodes, nodePieces, numPieces, root):
    for objectToProcess in range(0, len(geometryNodes)):
        refGeo = geometryNodes[objectToProcess]
        unpack = None
        deleteUnpack = None

        tempName = geometryNodes[objectToProcess].parent().name()

        stringInput = 'UNPACK{}'.format(objectToProcess)

        if(refGeo.parent().node(stringInput)  == None):
            unpack = refGeo.parent().createNode('unpack', stringInput)
        elif (refGeo.parent().node(stringInput)  != None):
            unpack = refGeo.parent().node(stringInput)
        else:
            print 'ERROR 0: Cannot generate unpack node!'

        unpack.setFirstInput(refGeo)

        #Locks the unpack node to prevent processing during FBX Export
        if(unpack.isHardLocked()):
            unpack.setHardLocked(False)
            unpack.setHardLocked(True)
        else:
            unpack.setHardLocked(True)

        for index in range(0, numPieces[objectToProcess]):
            proxy   = None
            delete  = None
            xform   = None

            #################################
            #Create the nodes to process the
            #individual pieces
            #################################
            proxy = nodePieces[objectToProcess][index].createNode('object_merge', 'PROXY')
            proxy.setParms({'objpath1':proxy.relativePathTo(unpack),
                            'xformtype':'object',
                            'xformpath':'../..'})

            delete = nodePieces[objectToProcess][index].createNode('delete', 'DELETE')
            delete.setParms({'group':'@name=piece{}'.format(index),
                            'negate':'keep'})
            delete.setFirstInput(proxy)

            xform = nodePieces[objectToProcess][index].createNode('xform', 'XFORM')

            #################################
            #This is important to grab the correct transform for the pieces.
            #Otherwise, all transforms will be at [0,0,0] and ruin your day.
            #The key here is finding the delta of the rest values between the
            #creation frame and the next frame.
            #################################
            xform.setFirstInput(delete)
            xform.setDisplayFlag(True)
            xform.setRenderFlag(True)
            xform.parm('movecentroid').pressButton()

            creationFrame = nodes[objectToProcess].parm('createframe').eval()
            dopxform1 = 0
            dopxform2 = 0
            deltaXFORM = []
            if nodes[objectToProcess].parent().parm('isplayer').eval():
                nodes[objectToProcess].parent().setParms({'isplayer':0})
                hou.setFrame(creationFrame)
                dopxform1 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
                nodes[objectToProcess].parent().setParms({'isplayer':1})
                hou.setFrame(creationFrame+1)
                dopxform2 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
                hou.setFrame(creationFrame)
            else:
                hou.setFrame(creationFrame)
                dopxform1 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
                hou.setFrame(creationFrame+1)
                dopxform2 = nodes[objectToProcess].simulation().findObject(nodes[objectToProcess].name()).geometry().iterPoints()[index].attribValue('rest')
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
            if(xform.parent().node('file1') != None):
                xform.parent().node('file1').destroy()
            xform.parent().layoutChildren()

def processMesh(nodes, nodePieces, numPieces):
    PARMS   =   ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'px', 'py', 'pz']
    RFSTART = int(hou.expandString('$RFSTART'))
    RFEND = int(hou.expandString('$RFEND'))

    for frame in range(RFSTART, RFEND+1):
        hou.setFrame(frame)
        print 'Processing Frame: {}'.format(frame)

        for objectToProcess in range(0, len(numPieces)):
            #If at the creation frame, skip keyframe
            if frame == nodes[objectToProcess].parm('createframe').eval():
                continue

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

    print 'Processing Complete!'
