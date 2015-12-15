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
    doptoolutils.genericTool(kwargs, 'staticobject')
    collisionMesh.setSelected(False)
    collisionMesh.setDisplayFlag(False)

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
                            'vm_samplesx':12,
                            'vm_samplesy':12,
                            'vm_variance':0.00001778279})

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
