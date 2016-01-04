import hou
import realtimetoolutils
reload(realtimetoolutils)

import toolutils
import doptoolutils
import dopparticlefluidtoolutils
import objecttoolutils

def splash(kwargs):
    collisionMesh = realtimetoolutils.createSimpleObject("sphere", [0,0,0], [0,0,0], [0.5,0.5,0.5])
    collisionMesh.setSelected(True)
    collisionMesh.displayNode().setParms({  'type':'polymesh',
                                            'rows':50,
                                            'cols':50})
    collisionMeshMountain = collisionMesh.displayNode().createOutputNode('mountain', 'mountainDeformer')
    collisionMeshMountain.setParms({'frac_depth':9,
                                    'rough':0.05,
                                    'height':0.184,
                                    'freq1':10,
                                    'freq2':10,
                                    'freq3':10})
    collisionMeshMountain.setDisplayFlag(True)
    doptoolutils.genericTool(kwargs, 'staticobject')
    collisionMesh.setSelected(False)
    collisionMesh.setDisplayFlag(False)
    collisionMesh.createNode('null', 'RENDER').setRenderFlag(True)
    collisionMesh.layoutChildren()

    sourceMesh = realtimetoolutils.createSimpleObject("sphere", [-2,-2,-2], [0,0,0], [0.25,0.25,0.25])
    sourceMesh.setSelected(True)

    objectnode = doptoolutils.genericDopConverterTool(toolutils.activePane(kwargs), 'flipfluidobject', 'flipfluidobject1', 'Select object to convert into a FLIP Fluid.  Press Enter to accept selection.')
    dopparticlefluidtoolutils.convertToFLIP(objectnode)

    flipObject = hou.selectedNodes()[0]
    flipObject.setParms({   'particlesep':0.025,
                            'initvel':True,
                            'velocityx':10,
                            'velocityy':10,
                            'velocityz':10})

    shopBasicLiquid = hou.node('/shop/basicliquid')
    shopBasicLiquid.setParms({  'diff_enable':False,
                                'spec_angle':10,
                                })

    #Generate Lights
    nodeLight = realtimetoolutils.createSimpleSpotLight([3.55555, 1.75684, 1.53865],
                                                        [-31.2195, 68.0879, 0],
                                                        10)

    #Generate Camera
    nodeCam = realtimetoolutils.createCamera(   [0,0,4.5],
                                                [0,0,0],
                                                1024)

    #Generate Renderer
    nodeMantra = realtimetoolutils.createMantraNode('/obj', nodeCam.path())
    nodeMantra.setParms({   'vm_renderengine':'pbrraytrace',
                            'vm_samplesx':3,
                            'vm_samplesy':3,
                            'vm_variance':0.01})

    #Move /shop into /obj/SHOP for organization
    nodeSHOP = hou.node('/obj').createNode('shopnet', 'SHADERS')
    nodesToCopy = [hou.node('/shop/basicliquid'), hou.node('/shop/uniformvolume')]
    hou.copyNodesTo(nodesToCopy, nodeSHOP)
    liquidShader = nodeSHOP.node('basicliquid')
    volumeShader = nodeSHOP.node('uniformvolume')

    nodeFluid = hou.node(sourceMesh.path() + '_fluid')
    nodeFluid.setParms({'shop_materialpath':liquidShader.path()})

    nodeInterior = hou.node(sourceMesh.path() + '_fluidinterior')
    nodeInterior.setParms({'shop_materialpath':volumeShader.path()})
    nodeInterior.setDisplayFlag(False)

    nodesToCopy[0].destroy()
    nodesToCopy[1].destroy()

    hou.node('/obj').layoutChildren()
    hou.setFrame(8)

    sourceMesh.setSelected(True)

def targetSplash(kwargs):
    framesToCollide = 12
    timeToCollide = framesToCollide/hou.fps()
    flipDOPNode = None
    flipObject = None
    staticObject = None
    gravityNode = None

    for i in hou.selectedNodes():
        if i.type().name() == 'staticobject':
            staticObject = hou.node(i.parm('objpath').unexpandedString())
        if i.type().name() == 'flipobject':
            flipDOPNode = i
            flipObject = hou.node(i.parm('soppath').unexpandedString())
        if i.type().name() == 'gravity':
            gravityNode = i

    hou.setFrame(1)

    targetPos = staticObject.worldTransform().extractTranslates()
    sourcePos = flipObject.worldTransform().extractTranslates()
    gravityVec = [  gravityNode.parm('forcex').eval(),
                    gravityNode.parm('forcey').eval(),
                    gravityNode.parm('forcez').eval()]

    velocityVector = [  -(sourcePos[0]-targetPos[0]+0.5*gravityVec[0]*timeToCollide**2)/timeToCollide,
                        -(sourcePos[1]-targetPos[1]+0.5*gravityVec[1]*timeToCollide**2)/timeToCollide,
                        -(sourcePos[2]-targetPos[2]+0.5*gravityVec[2]*timeToCollide**2)/timeToCollide]

    flipDOPNode.setParms({  'velocityx':velocityVector[0],
                            'velocityy':velocityVector[1],
                            'velocityz':velocityVector[2]})

    #TODO:temp.simulation().objects()[1].findSubData('Forces').subData()
    #TODO:^^Combine all acting forces
    #TODO:Store equation in initial velocity
    #TODO:Show trajectory via curve
