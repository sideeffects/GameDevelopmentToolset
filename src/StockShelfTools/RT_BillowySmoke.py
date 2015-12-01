import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def billowySmokeRT(kwargs, clustering=False):
    """ Selected object becomes an emitter of hot billowy smoke.
    """
    sceneviewer = toolutils.activePane(kwargs)

    if clustering == False:
        (source, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the source of the billowy smoke. The source must be an object. Press Enter to accept selection.")
    else:
        (source, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select object whose points will be used for billowy smoke clustering. Press Enter to accept selection.")

    sourcegeo = source.displayNode()

    kwargs['ctrlclick'] = True;

    # After calculating the boundingbox, reset sim, move timeline to frame 1
    hou.setFrame(1)

    #((pyronode, fieldnode), (uprespyronode, upresfieldnode)) = dopsmoketoolutils.buildFluidBoxWithUpres(kwargs, "pyro", buildmat=False)
    (pyronode, fieldnode) = dopsmoketoolutils.createEmptyFluidBox(sceneviewer, "pyro_build", buildmat=False)
    pyrosolver = doptoolutils.findSolverNode(pyronode, 'pyrosolver')

    # Set up land in node
    landinnode = pyrosolver

    # Resize the smoke box to contain our bounding box
    if hou.ui.orientationUpAxis() == hou.orientUpAxis.Z:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 0, 1.5*diam]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+2.5*diam, bbox.sizevec()[2]+4*diam])
    else:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 1.5*diam, 0]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+4*diam, bbox.sizevec()[2]+2.5*diam])


    # Introduce divdiam diameter for scaling fluidsource later on
    divdiam = diam

    # If clustering, append cluster nodes and make it the new source
    if clustering is True:
        sourcelist=cluster(sourcegeo)
        sourcegeo=sourcelist[0]
        sourcegeo.setDisplayFlag(True)
        source = sourcegeo.parent()
        pyronode.parm("instance_objects").set(1)
        pyronode.parm("instance_points").set(sourcelist[1].path())

        # Make sure to land on the cluster node
        landinnode = sourcelist[2]

        # Find out amount of clusters and recalculate cluster diameter
        # Based on the volume calculated from the original diameter
        clustercount = landinnode.evalParm("num_clusters")
        volumeratio = 1. / clustercount
        volumeratio = math.pow(volumeratio, 1.0/3.0)
        diam = diam * volumeratio
        # Because in clustering we tend to work with tighter
        # flames we want to further cut the diameter
        divdiam = diam/1.5
        diam /= 3.0

    # We want to be normalized to a unit sphere, so compute radius
    # here.
    diam = diam / 2.0
    divdiam /= 2.0

    #mat = dopsmoketoolutils.createBillowySmokeMaterial()
    #fieldnode.parent().parm('shop_materialpath').set(mat.path())

    # apply preset to smokesolver
    doppyrotoolutils.applyParmSet(pyrosolver, diam,
                [
                ('temp_diffusion', 0.4, doppyrotoolutils.op_mult),
                ('cooling_rate', 0.6, None),
                ('lift', 4.0, doppyrotoolutils.op_mult),
                ('enable_confinement',False,None),
                ('confinementscale', 4.0, None),
                ('conf_use_control_field',1,None),
                ('conf_control_field','density',None),
                ('conf_control_influence',0.75,None),
                ('conf_remap_control_field',1,None),
                ('turb_use_control_field', 1, None),
                ('turb_control_influence', 1.0, None),
                ('enable_dissipation',1,None),
                ('evap', 0.075, None),
                ('dissipation_control_range2', 2.0, None),
                ('enable_turbulence', 1, None),
                ('turbulence_scale', 0.25, None),
                ('turb_swirl_size', 1.5,doppyrotoolutils.op_mult ),
                ('turb_pulse_length', 0.5, None),
                ('turb_turb',3,None),
                ('turb_seed', 0.0, None),
                ('turb_guidestreamerlen', 1.0, None),
                ('enable_combustion',False,None),
                ('enable_disturbance',1,None),
                ('dist_scale',0.425,doppyrotoolutils.op_mult),
                ('dist_target',1,None),
                ('dist_density_cutoff',0.1,None),
                ('dist_block_size',0.3,doppyrotoolutils.op_mult),
                ('dist_use_control_field',1,None),
                ('dist_control_field','temperature',None),
                ('dist_control_influence',1.0,None),
                ('dist_control_range2',0.05,None),
                ('scaled_forces','* ^Gravity',None),
                ])

    #build confinement ramp
    doppyrotoolutils.buildRamp(pyrosolver, 'conf_control_field_ramp2', 'catmull-rom',
                [
                (0, 0),
                (0.06, 0.75),
                (0.15, 0.925),
                (0.9, 0.3),
                (1, 0),
                ])

    #build dissipation ramp
    doppyrotoolutils.buildRamp(pyrosolver, 'remap_dissipation_field', 'catmull-rom',
                [
                (0, 1),
                (0.17889, 0.875),
                (0.368, 0.270),
                (1, 0)
                ])

    #set divsize
    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.15,doppyrotoolutils.op_mult),
                ('multifield_rangemax',0.5,None),
                            ('multifield_densityscale',2.0,doppyrotoolutils.op_div),
                            ('multifield_shadowscale',0.25,doppyrotoolutils.op_div),
                ]
                )



    # Make our source the source
    convertmode = "SOP_Source_%s" % doppyrotoolutils.incominggeotype(sourcegeo)
    sourcenode = dopsmoketoolutils.convertObjectToSourceSink(pyronode, source, convertmode)


    # if a fluidsource is connected, set it up
    used = []
    fluidsource = toolutils.findOutputNodeOfType(sourcegeo,'fluidsource')
    if fluidsource != None:
            doppyrotoolutils.applyParmSet(fluidsource, divdiam,
                         [
                         ('use_noise',True,None),
                         ('voronoi_influence',0.3,None),
                         ('pulse_duration',5,None),
                         ('voronoi_influence',0.3,None),
                         ('cell_thresh',0.305,None),
                         ('cell_min',0.35,None),
                         ('pulse_duration',5,None),
                         ('size',0.2,doppyrotoolutils.op_mult),
                         ('edge_thickness',0.075,doppyrotoolutils.op_mult),
                         ('in_feather_length',0.1,doppyrotoolutils.op_mult),
                         ('element_size',1,doppyrotoolutils.op_mult),
                         ('cell_size',0.5,doppyrotoolutils.op_mult),
                         ('bandwidth',0.2,doppyrotoolutils.op_mult),
                         ('bound_expansion',0.05,doppyrotoolutils.op_mult),
                         ('bandwidth',0.2,doppyrotoolutils.op_mult),
                         ('feather',0.05,doppyrotoolutils.op_mult)
                         ])

            #link divsize parms
            fluidsource.parm("divsize").setExpression('ch("%s")' % pyronode.parm("divsize").path())


            if clustering is True:
                doppyrotoolutils.applyParmSet(fluidsource, diam,
                            [
                            ('enable_partitioning',True,None)
                            ])


    # if a clusternode is used, find it and set it up
    clusternode = toolutils.findInputNodeOfType(fluidsource, 'clusterpoints')
    if clusternode is not None:
        doppyrotoolutils.applyParmSet(clusternode, diam,
                [
                 ('size_paddingx',0.3,doppyrotoolutils.op_mult),
                 ('size_paddingy',0.3,doppyrotoolutils.op_mult),
                 ('size_paddingz',0.3,doppyrotoolutils.op_mult),
                 ('size_padding2x',0.3,doppyrotoolutils.op_mult),
                 ('size_padding2y',3,doppyrotoolutils.op_mult),
                 ('size_padding2z',0.3,doppyrotoolutils.op_mult),
                 ])

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
    pyrosolver.parent().layoutChildren()
    landinnode.setCurrent(True, True)
    toolutils.homeToSelectionNetworkEditorsFor(landinnode)
    sceneviewer.enterCurrentNodeState()
