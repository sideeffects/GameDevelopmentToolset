import hou
import objecttoolutils
import roptoolutils
import cop2toolutils
import objecttoolutils
import realtimetoolutils
reload(realtimetoolutils)

#TODO:Create $HIP/render folder

def flipbookRig(kwargs):
    realtimetoolutils.createProjectFolder("render")
    realtimetoolutils.createProjectFolder("exports")

    #Generate Camera
    fbCam = objecttoolutils.genericCameraLightTool(kwargs, "cam", "FLIPBOOK_CAM")
    fbCam.setParms({'resx':1024,
                    'resy':1024,
                    'projection':0,})

    #Generate ROP
    fbROP = hou.node("/obj").createNode("ropnet", "RENDER_NETWORK")
    fbMantra = fbROP.createNode("ifd", "RENDER_FRAMES")
    fbMantra.setParms({ 'camera':fbCam.path(),
                        'trange':1,
                        'vm_renderengine':'pbrmicropoly'})
    fbMantra.setParmExpressions({  'f1':"$RFSTART",
                                'f2':"$RFEND"})
    fbROP.layoutChildren()

    #Generate COP
    fbCOP = hou.node("/obj").createNode("cop2net", "COMPOSITE_NETWORK")
    fbFile = fbCOP.createNode("file", "renderFileImport")
    fbFile.setParms({"filename1":fbMantra.parm("vm_picture").unexpandedString()})

    fbMosaic = fbFile.createOutputNode("mosaic", "LAYOUT_IMAGES")
    fbMosaic.setParms({ 'numperline':8,
                        'imagelimit':64})

    fbOutput = fbMosaic.createOutputNode("rop_comp", "RENDER_FLIPBOOK")
    fbOutput.setParms({ 'trange':0,
                        'copoutput':"$HIP/exports/TEX_FB_SomeFlipbook.png"})
    fbCOP.layoutChildren()

    hou.node("/obj").layoutChildren([fbCam, fbROP, fbCOP])

    #Generate Environment Light
    sunNode = objecttoolutils.createSkyLight(kwargs)
