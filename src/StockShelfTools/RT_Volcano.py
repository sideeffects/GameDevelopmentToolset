import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def volcano(kwargs):
    """ Selected object becomes the source from which to build a
        volcano.
    """
    sceneviewer = toolutils.activePane(kwargs)

    (bomb, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the emitter of the volcano. The emitter must be an object, preferably rather large. Press Enter to accept selection.")
    bombgeo = bomb.displayNode()

    kwargs['ctrlclick'] = True;
    (pyronode, fieldnode) = dopsmoketoolutils.createEmptyFluidBox(sceneviewer, "pyro_build", buildmat=False)
    pyrosolver = doptoolutils.findSolverNode(pyronode, 'pyrosolver')

    # Resize the smoke box to contain our bounding box
    if hou.ui.orientationUpAxis() == hou.orientUpAxis.Z:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 0, 4*diam]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+6.5*diam, bbox.sizevec()[1]+6.5*diam, bbox.sizevec()[2]+9*diam])
    else:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 4*diam, 0]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+6.5*diam, bbox.sizevec()[1]+9*diam, bbox.sizevec()[2]+6.5*diam])

    # We want to be normalized to a unit sphere, so compute radius
    # here.
    diam = diam / 2.0

    #mat = createNewPyroShopPreset(pyrosolver, 'Volcano')
    #mat.setName('volcano_pyro', True)
    #fieldnode.parent().parm('shop_materialpath').set(mat.path())

    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.15,doppyrotoolutils.op_mult),
                ('velocity_voxelsample','faces',None),
                ('closedends', False, None),
                ('multifield_densityscale',1.0,doppyrotoolutils.op_div),
                ('multifield_shadowscale',1.0,doppyrotoolutils.op_div),
                ]
                )

    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('uniformdiv', 65, None),

                ])

    doppyrotoolutils.applyParmSet(pyrosolver, diam,
               [
               ('timescale', 1,None),
               ('temp_diffusion', 0.5,doppyrotoolutils.op_mult),
               ('cooling_rate', 0.75,None),
               ('lift', 5,doppyrotoolutils.op_mult),
               ('enable_combustion', 0, None),
               ('enable_disturbance', 1, None),
               ('dist_scale', 5, doppyrotoolutils.op_mult),
               ('dist_target', 'vel', None),
               ('dist_density_cutoff',0.1,None),
               ('dist_override_block_size',0,None),
               ('enable_sharpening', 1, None),
               ('sharpenrate', 2.0, None),
               ('enable_confinement', 1, None),
               ('enable_dissipation', 1, None),
               ('confinementscale', 2, None),
                ('scaled_forces','* ^Gravity',None),
               ]
               )

    # Set the timescale to run for 100 frames then slow down after preroll

    doppyrotoolutils.applyKeySet(pyrosolver, 'timescale',
                [
                (0,1),
                (3.999,1),
                (4,0.1)
                ]
                )

    # Make our bomb the source
    convertmode = "SOP_Source_%s" % doppyrotoolutils.incominggeotype(bombgeo)
    sourcenode = dopsmoketoolutils.convertObjectToSourceSink(pyronode, bomb, convertmode)

    # if a fluidsource is connected, set it up
    fluidsource = toolutils.findOutputNodeOfType(bombgeo,'fluidsource')
    if fluidsource != None:

                doppyrotoolutils.applyParmSet(fluidsource, diam,
                                         [
                                         ('use_noise',True,None),
                                         ('voronoi_influence',0.6,None),
                                         ('pulse_duration',1,None),
                                         ('cell_thresh',0.35,None),
                                         ('cell_min',0.35,None),
                                         ('element_size',1,doppyrotoolutils.op_mult),
                                         ('cell_size',0.5,doppyrotoolutils.op_mult),
                                         ('size',0.2,doppyrotoolutils.op_mult),
                                         ('edge_thickness',0.1,doppyrotoolutils.op_mult),
                                         ('in_feather_length',0.1,doppyrotoolutils.op_mult),
                                         ('bound_expansion',0.05,doppyrotoolutils.op_mult),
                                         ('bandwidth',0.2,doppyrotoolutils.op_mult),
                                         ('feather',0.05,doppyrotoolutils.op_mult)
                                         ])

                #link divsize parms
                fluidsource.parm("divsize").setExpression('ch("%s")' % pyronode.parm("divsize").path())

    # Try to find resize node (solver) and setup parms
    resizenode = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    if resizenode != None:
        doppyrotoolutils.applyParmSet(resizenode, diam,
                     [
                     ('bound_padding', 0.4, doppyrotoolutils.op_mult),
                     ('bound_mode',1,None),
                     ('operator_path',bomb.path(),None)
                     ])

    # Switch the selection to the pyrosolver as that is where all
    # the juiciest parms are.
    pyrosolver.setCurrent(True, True)
    pyrosolver.parent().layoutChildren()
    sceneviewer.enterCurrentNodeState()
