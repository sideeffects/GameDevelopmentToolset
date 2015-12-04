import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def burn(kwargs,smokeon=True,clustering=False):
    """ Selected object becomes a continuous source of fuel igniting
        on creation.
    """
    sceneviewer = toolutils.activePane(kwargs)

    if clustering == False:
        (fuel, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the object to burn. Press Enter to accept selection.")
    else:
        (fuel, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select object whose points will be used for fire clustering. Press Enter to accept selection.")

    fuelgeo = fuel.displayNode()

    # After calculating the boundingbox, reset sim, move timeline to frame 1
    hou.setFrame(1)

    kwargs['ctrlclick'] = True;
    (pyronode, fieldnode) = dopsmoketoolutils.createEmptyFluidBox(sceneviewer, "pyro_build", buildmat=False)
    pyrosolver = doptoolutils.findSolverNode(pyronode, 'pyrosolver')

    # Define Land In Node
    landinnode = pyrosolver

    # Resize the smoke box to contain our bounding box
    if hou.ui.orientationUpAxis() == hou.orientUpAxis.Z:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 0, 2.5*diam]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+2.5*diam, bbox.sizevec()[2]+5.5*diam])
    else:
        pyronode.parmTuple("t").set(bbox.center() + hou.Vector3([0, 2.5*diam, 0]))
        pyronode.parmTuple("size").set([bbox.sizevec()[0]+2.5*diam, bbox.sizevec()[1]+5.5*diam, bbox.sizevec()[2]+2.5*diam])

    # Introduce divdiam diameter for scaling fluidsource later on
    divdiam = diam

    # If clustering is enabled, append cluster node and use clusterpoints as source
    if clustering is True:
        fuellist=cluster(fuelgeo)
        fuelgeo=fuellist[0]

        # Make sure the displayflag is set to the cluster points
        fuel = fuelgeo.parent()
        fuelgeo.setDisplayFlag(True)
        fuelgeo.setRenderFlag(True)

        pyronode.parm("instance_objects").set(1)
        pyronode.parm("instance_points").set(fuellist[1].path())

        # Change Node To Land In
        landinnode = fuellist[2]

        # Find out amount of clusters and recalculate cluster diameter
        # Based on the volume calculated from the original diameter
        # In order to make sure divisions don't get to small, clamp
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
    divdiam = divdiam / 2.0


    if smokeon:
        (mat, matcreated) = dopsmoketoolutils.findOrCreateMaterial('flames', 'flames')
    else:
        (mat, matcreated) = dopsmoketoolutils.findOrCreateMaterial('smokelessflames', 'smokelessflames')
    fieldnode.parent().parm('shop_materialpath').set(mat.path())
    if matcreated:
        copy_parm = mat.parm('copy_other1')
        if copy_parm is not None:
            copy_parm.set(pyronode.path())

    doppyrotoolutils.applyParmSet(pyrosolver, diam,
                 [
                 ('temp_diffusion',0.125,doppyrotoolutils.op_mult),
                 ('cooling_rate',0.8,None),
                 ('lift',4.5,doppyrotoolutils.op_mult),
                 ('confinementscale',2.0,None),
                 ('fuelinefficiency', 0.20000000000000001, None),
                 ('heatoutput', 0.15, None),
                 ('cooldown_time', 3.5, None),
                 ('fuel_speed', 0.050000000000000003, None),
                 ('cooling_field_range2',2,None ),
                 ('enable_shredding', 1, None),
                 ('shred_scale', 0.59999999999999998, doppyrotoolutils.op_multsquare),
                 ('gasrelease',14,None),
                 ('shred_stretch', 0.25, None),
                 ('shred_control_influence', 0.25, None),
                 ('emit_smoke',smokeon, None),
                 ('enable_disturbance',True,None),
                 ('dist_scale',0.4,doppyrotoolutils.op_mult),
                 ('dist_block_size',0.3,doppyrotoolutils.op_mult),
                 ('dist_density_cutoff',0.1,None),
                 ('dist_target',1,None),
                 ('scaled_forces','* ^Gravity',None),
                 ]
                 )

    doppyrotoolutils.buildRamp(pyrosolver, 'remap_dissipation_field', 'catmull-rom',
                [
                (0, 1),
                (0.17889, 0.875),
                (0.368, 0.270),
                (1, 0)
                ])

    doppyrotoolutils.buildRamp(pyrosolver, 'remap_cooldown_time', 'catmull-rom',
                [
                (1, 0.1),
                (0.511712, 0.3125),
                (0.306306, 0.79),
                (0.108108, 0.95),
                (0, 1),
                ])

    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.2,doppyrotoolutils.op_mult),
                ('velocity_voxelsample','center',None)
                ]
                )

    # Set Density to Heat if smokeless flame
    if smokeon is False:
        pyronode.parm("multifield_densityfield").set("heat")
        # Turn off the import of smoke so Mantra won't be confused
        ionode = toolutils.findChildNodeOfType(fieldnode.parent(), 'dopio')
        if ionode is not None:
            ionode.parm('enable1').set(False)

    doppyrotoolutils.applyParmSet(pyronode, diam,
         [
            ('multifield_densityscale',0.375,doppyrotoolutils.op_div),
            ('multifield_shadowscale',0.375,doppyrotoolutils.op_div),
            ('multifield_emitscale',5.0,doppyrotoolutils.op_div),
         ])

    # Make our fuel the source
    convertmode = "SOP_Source_%s" % doppyrotoolutils.incominggeotype(fuelgeo)
    sourcenode = dopsmoketoolutils.convertObjectToSourceSink(pyronode, fuel, convertmode)

    # Set up gasresize
    #gasresize = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    #if gasresize != None:
    #    gasresize.parm("bound_mode").set(2)
    #    gasresize.parm("operator_path").set(sourcenode.path())

    # if a fluidsource is connected, set it up
    used = []
    fluidsource = toolutils.findOutputNodeOfType(fuelgeo,'fluidsource')
    if fluidsource != None:

                doppyrotoolutils.applyParmSet(fluidsource, divdiam,
                                         [
                                         ('use_noise',True,None),
                                         ('voronoi_influence',0.3,None),
                                         ('pulse_duration',1,None),
                                         ('voronoi_influence',0.3,None),
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

        lookupfield = 'density'
        if smokeon == False:
            lookupfield = 'heat'

        doppyrotoolutils.applyParmSet(resizenode, diam,
                     [
                     ('bound_padding', 0.4, doppyrotoolutils.op_mult),
                     ('bound_mode',2,None),
                     ('reference_field',lookupfield,None),
                     ('operator_path',fuel.path(),None)
                     ])

    # Switch the selection to the pyrosolver as that is where all
    # the juiciest parms are.
    pyrosolver.parent().layoutChildren()
    landinnode.setCurrent(True, True)
    toolutils.homeToSelectionNetworkEditorsFor(landinnode)
    sceneviewer.enterCurrentNodeState()
