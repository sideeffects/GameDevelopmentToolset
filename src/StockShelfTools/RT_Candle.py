import hou
import toolutils
import doptoolutils
import dopsmoketoolutils
import doppyrotoolutils

def candleRT(kwargs,smokeon=False):
    """ Selected object becomes a small continuous source of fuel igniting
        on creation.
    """

    sceneviewer = doppyrotoolutils.toolutils.activePane(kwargs)

    (fuel, bbox, diam) = doppyrotoolutils.selectObject(kwargs, "Select the object to burn. Press Enter to accept selection.")
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

    # We want to be normalized to a unit sphere, so compute radius
    # here.
    diam = diam / 2.0

    (mat, matcreated) = dopsmoketoolutils.findOrCreateMaterial('candle', 'candle')
    fieldnode.parent().parm('shop_materialpath').set(mat.path())
    if matcreated:
        copy_parm = mat.parm('copy_other1')
        if copy_parm is not None:
            copy_parm.set(pyronode.path())

    doppyrotoolutils.applyParmSet(pyrosolver, diam,
                [
                    ('temp_diffusion',1.0,doppyrotoolutils.op_mult),
                    ('cooling_rate',0.6,None),
                    ('lift',15.0,doppyrotoolutils.op_mult),
                    ('burnrate',0.75,None),
                    ('fuelinefficiency',0.0,None),
                    ('heatoutput',0.5,None),
                    ('gasrelease',1.0,None),
                    ('cooldown_time',0.5,None),
                    ('cooling_field_range2',2.0,None),
                    ('emit_smoke',0,None),
                    ('heat_cutoff',0.1,None),
                    ('blend',0.5,None),
                    ('advect_fuel',1,None),
                    ('fuel_speed',0.5,None),
                    ('enable_disturbance',1,None),
                    ('dist_scale',2.0,doppyrotoolutils.op_mult),
                    ('shred_scale',0.6,doppyrotoolutils.op_multsquare),
                    ('confinementscale',2.0,None),
                    ('wind_21',1,None),
                    ('dist_target',1,None),
                    ('dist_density_cutoff',0.2,None),
                    ('dist_block_size',0.4,doppyrotoolutils.op_mult),
                    ('dist_thresh_field','temperature',None),
                    ('shred_stretch',0.25,None),
                    ('shred_control_influence',0.25,None),
                     ('scaled_forces','* ^Gravity',None),
                ]
                                )

    doppyrotoolutils.buildRamp(pyrosolver, 'remap_cooldown_time', 'catmull-rom',
                [
                (1, 0.25),
                (0.7, 0.3125),
                (0.306306, 0.79),
                (0.108108, 0.95),
                (0, 1),
                ])

    doppyrotoolutils.applyParmSet(pyronode, diam,
                [
                ('divsize',0.15,doppyrotoolutils.op_mult),
                ('velocity_voxelsample','center',None),
                ('multifield_showguide',1,None),
                ('density_showguide',0,None),
                ('multifield_usebox',1,None),
                ('multifield_useboxhash',1,None),
                ('multifield_densityfield','heat',None),
                ('multifield_densityscale',1.0,doppyrotoolutils.op_div),
                ('multifield_shadowscale',1.0,doppyrotoolutils.op_div),
                ('multifield_emitscale',5.0,doppyrotoolutils.op_div),
                ('multifield_emitfield','temperature',None),
                ('multifield_emitcdfield','heat',None),
                ('multifield_emitcdrangeoverride',1,None),
                ('multifield_emitcdrange2',1,None),
                ('multifield_emitrangeoverride',1,None),
                ('multifield_emitrange2',2.5,None),
                ('multifield_emitcdpreset',4,None)
                ]
                )

    doppyrotoolutils.buildRamp(pyronode, 'multifield_emitramp', 'catmull-rom',
                [
                (1, 1),
                (0.473301, 1),
                (0.449029, 0.46),
                (0.402913, 0.133),
                (0.339806, 0),
                (0,0),
                ])

    doppyrotoolutils.buildColorRamp(pyronode, 'multifield_emitcdramp','catmull-rom',
                        [
                            (0.0485437,(0.964421, 0.404564, 0.0195433)),
                            (0.038835,(0.0, 0.0, 0.0)),
                            (0.0800971,(1, 0.731, 0)),
                            (0.184466,(1, 0.8833, 0.731)),
                            (1,(0.652, 0.8318, 1)),
                        ])

    # Make our fuel the source
    convertmode = "SOP_Source_%s" % doppyrotoolutils.incominggeotype(fuelgeo)
    sourcenode = dopsmoketoolutils.convertObjectToSourceSink(pyronode, fuel, convertmode)

    # Turn off the import of smoke so Mantra won't be confused
    ionode = doppyrotoolutils.toolutils.findChildNodeOfType(fieldnode.parent(), 'dopio')
    if ionode is not None:
        ionode.parm('enable1').set(False)

    # if a fluidsource is connected, set it up
    fluidsource = doppyrotoolutils.toolutils.findOutputNodeOfType(fuelgeo,'fluidsource')
    if fluidsource != None:
                doppyrotoolutils.applyParmSet(fluidsource, diam,
                         [
                         ('use_noise',False,None),
                         ('divsize',0.075,doppyrotoolutils.op_mult),
                         ('size',0.1,doppyrotoolutils.op_mult),
                         ('edge_thickness',0.06,doppyrotoolutils.op_mult),
                         ('eloc',0.025,None),
                         ('e_interior',0,None),
                         ('in_feather_length',0.06,doppyrotoolutils.op_mult),
                         ('bound_expansion',0.05,doppyrotoolutils.op_mult),
                         ('bandwidth',0.1,doppyrotoolutils.op_mult),
                         ('feather',0.0325,doppyrotoolutils.op_mult)
                         ])

                #link divsize parms
                fluidsource.parm("divsize").setExpression('ch("%s")' % pyronode.parm("divsize").path())

    # Try to find resize node (solver) and setup parms
    resizenode = doptoolutils.findSolverInInput(pyrosolver,'gasresizefluiddynamic')
    if resizenode != None:

        doppyrotoolutils.applyParmSet(resizenode, diam,
                     [
                     ('bound_padding', 0.4, doppyrotoolutils.op_mult),
                     ('bound_mode',2,None),
                     ('reference_field','heat',None),
                     ('operator_path',fuel.path(),None),
                     ('field_cutoff',0.01,None),
                     ])

    # Switch the selection to the pyrosolver as that is where all
    # the juiciest parms are.
    pyrosolver.parent().layoutChildren()
    landinnode.setCurrent(True, True)
    doppyrotoolutils.toolutils.homeToSelectionNetworkEditorsFor(landinnode)
    sceneviewer.enterCurrentNodeState()
