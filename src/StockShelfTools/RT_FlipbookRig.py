import hou
import objecttoolutils
import realtimetoolutils

#TODO:Create $HIP/render folder

def flipbookRig(kwargs, setCamPos = False, camPos = [0,0,0]):
    '''
    This function generates a basic flipbook setup. It'll create:
    -Camera
    -ROP Network with Mantra node
    -COP Network with required nodes for flipbooking

    setCamPos: True/False
    For the preset modules. If False, generate camera at viewport location.
    If True, explicitly set camera position via python.

    camPos: [x,y,z] coordinates for the camera position. Pipe in if setCamPos = True.
    '''

    realtimetoolutils.createProjectFolder("render")
    realtimetoolutils.createProjectFolder("exports")

    #Generate Camera
    fbCam = objecttoolutils.genericCameraLightTool(kwargs, "cam", "FLIPBOOK_CAM")
    fbCam.setParms({'resx':1024,
                    'resy':1024,
                    'projection':0,})

    if setCamPos:
        fbCam.setParms({'tx':camPos[0],
                        'ty':camPos[1],
                        'tz':camPos[2]})

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
