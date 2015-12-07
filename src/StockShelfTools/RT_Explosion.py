import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def explosion(kwargs):
    """ Selected object becomes the bomb from which to build a
        explosion.
    """
    sceneviewer = toolutils.activePane(kwargs)

    (bomb, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the base of the fireball. The base must be an object. Press Enter to accept selection.")
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

    (mat, matcreated) = dopsmoketoolutils.findOrCreateMaterial('fireball', 'fireball')
    fieldnode.parent().parm('shop_materialpath').set(mat.path())
    if matcreated:
        copy_parm = mat.parm('copy_other1')
        if copy_parm is not None:
            copy_parm.set(pyronode.path())
    doppyrotoolutils.applyParmSet(mat, diam,
                [
                ('s_amp', 15, None),
                ('fi_amp', 5, None)
                ])


    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.1,doppyrotoolutils.op_mult),
                ('sizex', 15, None),
                ('sizey', 15, None),
                ('sizez', 15, None),
                ('tx', 0, None),
                ('ty', 0, None),
                ('tz', 0, None),
                ('velocity_voxelsample','faces',None),
                ('closedends', False, None),
                ('multifield_densityscale',0.3,doppyrotoolutils.op_div),
                ('multifield_shadowscale',0.3,doppyrotoolutils.op_div),
                ('multifield_cdfield','density',None),
                ('multifield_emitfield','heat',None),
                ('multifield_emitscale',1.5,doppyrotoolutils.op_div),
                ('multifield_emitcdfield','temperature',None),
                ('multifield_emitcdrange2',5,None)
                ]
                )
    doppyrotoolutils.buildColorRamp(pyronode, 'multifield_cdramp', 'catmull-rom',
                [
                (0,     (0.15, 0.15, 0.15)),
                ])

    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('uniformdiv', 65, None),

                ])

    doppyrotoolutils.applyParmSet(pyrosolver, diam,
               [
               ('timescale', 0.65,None),
               ('temp_diffusion', 0.05,doppyrotoolutils.op_mult),
               ('cooling_rate', 0.7,None),
               ('lift', 0,doppyrotoolutils.op_mult),
               ('fuelinefficiency', 0.3,None),
               ('heatoutput', 0.3,None),
               ('gasrelease', 100.0,None),
               ('cooldown_time',6.0,None),
               ('cooling_field_range2', 3.0,None),
               ('use_dense', 1,None),
               ('heat_cutoff', 0.8,None),
               ('blend', 1.0,None),
               ('fuel_speed', 0.05,None),
               ('enable_disturbance', 1, None),
               ('dist_scale', 0.75, None),
               ('dist_density_cutoff',0.125,None),
               ('dist_target',0,None),
               ('dist_block_size',0.2,None),
               ('enable_shredding', 1, None),
               ('shred_scale', 1.0, doppyrotoolutils.op_multsquare),
               ('enable_turbulence', 1, None),
               ('turbulence_scale', 0.75, None),
               ('enable_confinement', 1, None),
               ('confinementscale', 2.5, None),
               ('dissipation_control_range2', 3.0,None),
               ('shred_stretch', 0.25, None),
               ('clip_value', 10.0, doppyrotoolutils.op_div),
               ('shred_control_influence', 0.25, None),
               ('turb_swirl_size', 0.5, doppyrotoolutils.op_mult),
               ('turb_rough', 0.35,None),
               ('turb_control_influence', 1.0, None),
               ('turb_remap_control_field', 1, None),
               ('turb_guidestreamerlen', 2.3,None),
                ('scaled_forces','* ^Gravity',None),
               ]
               )

    doppyrotoolutils.applyKeySet(pyrosolver, 'gasrelease',
                [
                (0,100),
                (0.375,20.74),
                (2.041,14)
                ]
                )

    doppyrotoolutils.buildRamp(pyrosolver, 'remap_dissipation_field', 'catmull-rom',
                [
                (1, 0.2),
                (0,1)
                ])

    doppyrotoolutils.buildRamp(pyrosolver, 'turb_control_ramp', 'catmull-rom',
                [
                (1, 0.667),
                (0.29,0.79),
                (0.0776,0.520),
                (0,0)
                ])

    doppyrotoolutils.buildRamp(pyrosolver, 'remap_cooldown_time', 'catmull-rom',
                [
                (1, 0.1),
                (0.511,0.3125),
                (0,1)
                ])

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
                                         ('feather',0.05,doppyrotoolutils.op_mult),
                                         #'scale',1.95,None)
                                         ])
                #link divsize parms
                fluidsource.parm("divsize").setExpression('ch("%s")' % pyronode.parm("divsize").path())

    # Try to find sourcevolume node (solver) and setup source key frames
    sourcevolume = doptoolutils.findSolverInInput(pyrosolver,'sourcevolume')
    if sourcevolume != None:
        doppyrotoolutils.applyKeySet(sourcevolume, 'scale_source',[
                    (0.0,1.0),
                    (24.0,0.0)
        ])
        # doppyrotoolutils.applyKeySet(sourcevolume,'scale_source',
        #             [
        #             (0.000000, 1.000000),
        #             (0.166667, 2.000000),
        #             (0.375000, 0.000000),
        #             (2.041667, 0.451193),
        #             (4.125000, 0.750000),
        #             (5.166667, 0.400000),
        #             (6.208333, 0.649445),
        #             (7.250000, 0.250000),
        #             (8.083333, 0.100000),
        #             (8.375000, 0.705150)
        #             ])

    # Try to find resize node (solver) and setup parms
    resizenode = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    if resizenode != None:
        doppyrotoolutils.applyParmSet(resizenode, diam,
                     [
                     ('bound_padding', 0.4, doppyrotoolutils.op_mult),
                     ('bound_mode',2,None),
                     ('operator_path',bomb.path(),None)
                     ])



    # Switch the selection to the pyrosolver as that is where all
    # the juiciest parms are.
    pyrosolver.setCurrent(True, True)
    pyrosolver.parent().layoutChildren()
    sceneviewer.enterCurrentNodeState()
