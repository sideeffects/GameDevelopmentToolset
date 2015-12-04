import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def dryice(kwargs):
    """ Selected object becomes an emitter of cold dry ice.
    """
    sceneviewer = toolutils.activePane(kwargs)

    (source, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the source of the dry ice. The source must be an object. Press Enter to accept selection.")
    sourcegeo = source.displayNode()


    kwargs['ctrlclick'] = True;

    # After calculating the boundingbox, reset sim, move timeline to frame 1
    hou.setFrame(1)

    #((pyronode, fieldnode), (uprespyronode, upresfieldnode)) = dopsmoketoolutils.buildFluidBoxWithUpres(kwargs, "pyro", buildmat=False)
    (pyronode, fieldnode) = dopsmoketoolutils.createEmptyFluidBox(sceneviewer, "pyro_build", buildmat=False)

    pyrosolver = doptoolutils.findSolverNode(pyronode, 'pyrosolver')


    # Resize the smoke box to contain our bounding box
    if hou.ui.orientationUpAxis() == hou.orientUpAxis.Z:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 0, -(1*diam)]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+2.5*diam, bbox.sizevec()[2]+4*diam])
    else:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, -(1*diam), 0]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+4*diam, bbox.sizevec()[2]+2.5*diam])

    # We want to be normalized to a unit sphere, so compute radius
    # here.
    diam = diam / 2.0

    #mat = dopsmoketoolutils.createBillowySmokeMaterial()
    #fieldnode.parent().parm('shop_materialpath').set(mat.path())

    # apply preset to smokesolver
    doppyrotoolutils.applyParmSet(pyrosolver, diam,
                [
                ('temp_diffusion', 0.65, doppyrotoolutils.op_mult),
                ('cooling_rate', 0.65, None),
                ('lift', 4.0, doppyrotoolutils.op_mult),
                ('enable_combustion', 0, None),
                ('evap', 0.06, None),
                ('enable_disturbance', 1, None),
                ('dist_scale', 1.0, None),
                ('dist_target',0,None),
                ('enable_sharpening', 1, None),
                ('sharpenrate', 0.65, None),
                ('enable_turbulence', 1, None),
                ('turbulence_scale', 0.2, None),
                ('confinementscale', 4.0, None),
                ('dissipation_control_range1', -0.45, None),
                ('dissipation_control_range2', 0.0, None),
                ('dist_density_cutoff', 0.1, None),
                ('shred_temp_threshold', -0.25, None),
                ('sharpen_locality', 2, None),
                ('turb_turb', 3, None),
                ('turb_swirl_size',1.0,doppyrotoolutils.op_mult),
                ('turb_control_influence', 1.0, None),
                ('turb_guidestreamerlen', 3.5, None),
                ('turb_density_field', 'density', None),
                ('conf_use_control_field', 1, None),
                ('conf_control_field', 'density', None),
                ('conf_control_influence', 0.75, None),
                ('conf_remap_control_field', 1, None),
                 ('scaled_forces','* ^Gravity',None),
                ])

    #build dissipation ramp
    doppyrotoolutils.buildRamp(pyrosolver, 'remap_dissipation_field', 'catmull-rom',
                [
                (0, 1),
                (0.1, 0.8125),
                (0.241, 0.270),
                (0.33, 0.729),
                (0.62, 0.27),
                (0.72,0.5),
                (1,0.15)
                ])


    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.15,doppyrotoolutils.op_mult),
                ('multifield_densityscale',1.0,doppyrotoolutils.op_div),
                ('multifield_shadowscale',1.0,doppyrotoolutils.op_div),
                ]
                )

    # Make our smokeobject the source
    convertmode = "SOP_Source_%s" % doppyrotoolutils.incominggeotype(sourcegeo)
    sourcenode = dopsmoketoolutils.convertObjectToSourceSink(pyronode, source, convertmode)

    # Set up gasresize
    gasresize = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    if gasresize != None:
        gasresize.parm("bound_mode").set(2)
        gasresize.parm("operator_path").set(source.path())

    # if a fluidsource is connected, set it up
    used = []
    fluidsource = toolutils.findOutputNodeOfType(sourcegeo,'fluidsource')
    if fluidsource != None:

            doppyrotoolutils.applyParmSet(fluidsource, diam,
                         [
                         ('use_noise',True,None),
                         ('voronoi_influence',0.3,None),
                         ('pulse_duration',5,None),
                         ('voronoi_influence',0.3,None),
                         ('cell_thresh',0.305,None),
                         ('cell_min',0.35,None),
                         ('divsize',0.075,doppyrotoolutils.op_mult),
                         ('pulse_duration',5,None),
                         ('edge_thickness',0.075,doppyrotoolutils.op_mult),
                         ('in_feather_length',0.1,doppyrotoolutils.op_mult),
                         ('size',0.2,doppyrotoolutils.op_mult),
                         ('element_size',1,doppyrotoolutils.op_mult),
                         ('cell_size',0.5,doppyrotoolutils.op_mult),
                         ('bandwidth',0.2,doppyrotoolutils.op_mult),
                         ('bound_expansion',0.05,doppyrotoolutils.op_mult),
                         ('bandwidth',0.2,doppyrotoolutils.op_mult),
                         ('feather',0.05,doppyrotoolutils.op_mult)
                         ])

            #link divsize parms
            fluidsource.parm("divsize").setExpression('ch("%s")' % pyronode.parm("divsize").path())

    # Try to find the volumesource solver and set the merge source option
    volumesource = doptoolutils.findSolverInInput(pyrosolver,'sourcevolume')
    if volumesource != None:
        volumesource.parm("source_merge").set('max')
        volumesource.parm("scale_temperature").set(-0.45)
        volumesource.parm("scale_source").set(2)



    # Try to find resize node (solver) and setup parms
    resizenode = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    if resizenode != None:
        doppyrotoolutils.applyParmSet(resizenode, diam,
                     [
                     ('bound_padding', 0.4, doppyrotoolutils.op_mult),
                     ('bound_mode',2,None),
                     ('operator_path',source.path(),None)
                     ])


    # Switch the selection to the pyrosolver as that is where all
    # the juiciest parms are.
    #pyrosolver.setCurrent(True, True)

    pyrosolver.setCurrent(True, True)
    pyrosolver.parent().layoutChildren()
    sceneviewer.enterCurrentNodeState()
