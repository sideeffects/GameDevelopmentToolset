'''VertexAnimationRig

This tool is designed to take a SOP level vertex animation and prepare a subnet that can be exported as an FBX. The resulting FBX will contain the animated skeleton with skinned geometry. In its current form, it generates 1 bone per point.
'''
import hou

import RealTimeVFXToolset

reload(RealTimeVFXToolset)

def init(nodes):
    geometryNodes = RealTimeVFXToolset.findNonDOPGeometry(nodes, None, 'dopobject')

    if geometryNodes == None:
        return 'Error: No geometry found!'

    bones = []
    subnet = hou.node('/obj').createNode('subnet', 'FBX_RESULT')

    root = subnet.createNode('bone', 'root')
    root.setParms({ 'crscalex':0,
                    'crscaley':0,
                    'crscalez':0})

    for node in geometryNodes:
        for idx, point in enumerate(node.geometry().points()):
            bones.append(subnet.createNode('bone', 'point{}'.format(idx)))
            bones[idx].setParms({'keeppos':True,
                                'tx':point.position()[0],
                                'ty':point.position()[1],
                                'tz':point.position()[2],
                                'crscalex':0.001,
                                'crscaley':0.001,
                                'crscalez':0.001
                                })
            bones[idx].setFirstInput(root)

    processSkeleton(nodes[0], bones)
    processMesh(geometryNodes[0], subnet)
    RealTimeVFXToolset.keyframeReducer(bones, ['tx', 'ty', 'tz'])
    subnet.layoutChildren()

def processSkeleton(clothNode, boneList):
    PARMS   =   ["tx", "ty", "tz"]
    RFSTART = int(hou.expandString('$RFSTART'))
    RFEND = int(hou.expandString('$RFEND'))

    for frame in range(RFSTART, RFEND+1):
        hou.setFrame(frame)
        print 'Processing Frame: {}'.format(frame)

        for idx, bone in enumerate(boneList):
            for indexParm in range(0,3):
                hou_keyed_parm = bone.parm(PARMS[indexParm])
                hou_keyframe = hou.Keyframe()
                hou_keyframe.setFrame(frame)
                hou_keyframe.setValue(clothNode.geometry().iterPoints()[idx].attribValue('P')[indexParm])
                hou_keyed_parm.setKeyframe(hou_keyframe)

    hou.setFrame(RFSTART)

    print "Processing Complete!"

def processMesh(geometryNode, fbxNode):
    geoNode = fbxNode.createNode('geo', 'GEOMETRY')

    #################################
    #Delete original file node
    #################################
    if(geoNode.node('file1') != None):
        geoNode.node("file1").destroy()

    objectMerge = geoNode.createNode('object_merge', 'GeometryImport')
    objectMerge.setParms({'objpath1':objectMerge.relativePathTo(geometryNode)})
    objectMerge.setHardLocked(True)

    capture = objectMerge.createOutputNode('capture', 'Capture')
    capture.setParms({'rootpath': '../../root'})
    capture.setHardLocked(True)

    for index in range(0,len(capture.geometry().points())):
        if len(capture.geometry().points()[index].attribValue('boneCapture')) > 2:
            print "Warning: Multiple weights assigned to the same point!"
            print "Warning: May contain animation errors."
            break

    deform = capture.createOutputNode('deform', 'Deform')
    deform.setDisplayFlag(True)
    deform.setRenderFlag(True)
