import hou

class BillowySmoke():
    sourceNode = None
    simulationNode = None

    #Source
    fluidSourceParms1 = {   "number_of_volumes":2,
                            "divsize":0.1,
                            "use_noise":1,
                            "voronoi_influence":0.3,
                            "pulse_duration":5,
                            "cell_thresh":0.305,
                            "cell_min":0.35}
    fluidSourceParms2 = {   "name2":"temperature"}

    #Simualtions
    gravityParms = {"uniquedataname":0}
    sourceVolumeParms = {   "velocity_merge":"add",
                            "vel_mask":"density"}

    pyroSolverSimulation = {"timescale":1,
                            "temp_diffusion":0.4,
                            "cooling_rate":0.6,
                            "viscosity":0,
                            "lift":0,
                            "buoyancy_dirx":0,
                            "buoyancy_diry":0,
                            "buoyancy_dirz":0}

    pyroSolverCombustion = {"enable_combustion":"0"}

    pyroSolverShape = { "enable_dissipation":"1",
                        "evap":0.075,
                        "enable_disturbance":"1",
                        "dist_scale":0.425,
                        "enable_shredding":"0",
                        "shred_scale":0.5,
                        "enable_sharpening":"0",
                        "sharpenrate":0.5,
                        "enable_turbulence":"1",
                        "turbulence_scale":0.25,
                        "enable_confinement":"0",
                        "confinementscale":4,

                        "dist_density_cutoff":0.1,
                        "dist_block_size":0.3,
                        "dist_use_control_field":1,
                        "dist_control_field":"temperature",
                        "dist_control_influence":1,
                        "dist_control_range1":0,
                        "dist_control_range2":0.05,

                        "turb_swirl_size":1.5,
                        "turb_turb":3,
                        "turb_control_influence":1}

    pyroSolverAdvanced = {"scaled_forces":"* ^Gravity"}

    pyroSmokeObject = { "divsize":0.1,
                        "sizex":10,
                        "sizey":10,
                        "sizez":10}

    resizeContainerParms = {"bound_padding":0.4,
                            "bound_mode":2,}

    def __init__(self, parent=None):
        self.CommandStack()

    def CommandStack(self):
        if self.CheckForSource():
            self.ConstructFuelSource()
            self.ConstructSimulation()
        else:
            print "Error! See Above."

    def CheckForSource(self):
        self.sourceNode = hou.selectedNodes()

        if len(self.sourceNode) > 1:
            print "Please select 1 geo node!"
            return False
        elif len(self.sourceNode) < 1:
            print "Please select 1 geo node!"
            return False
        else:
            self.sourceNode = self.sourceNode[0]
            return True

    def ConstructFuelSource(self):
        temp = self.sourceNode.displayNode().createOutputNode("fluidsource", "create_density_volume")
        temp.setParms(self.fluidSourceParms1)
        #TODO:Make this a better reference...probably after generating nodes
        temp.setParmExpressions({"divsize":'ch("/obj/SIMULATION/pyro/divsize")'})
        temp.cook(True)
        temp.setParms(self.fluidSourceParms2)
        temp.setDisplayFlag(True)
        self.sourceNode.displayNode().createOutputNode("merge", "merge_density_volumes").setDisplayFlag(True)
        self.sourceNode.displayNode().createOutputNode("null", "OUT_density").setDisplayFlag(True)
        self.sourceNode.createNode("null", "RENDER").setRenderFlag(True)

        # self.CreateNodeInline("fluidsource", "create_density_volume", self.sourceNode.displayNode(), True, False)
        # self.CreateNodeInline("merge", "merge_density_volumes", self.sourceNode.displayNode(), True, False)
        # self.CreateNodeInline("null", "OUT_density", self.sourceNode.displayNode(), True, False)
        # self.CreateNodeInline("null", "RENDER", self.sourceNode.displayNode(), False, True, False)
        self.sourceNode.layoutChildren()

    def ConstructSimulation(self):
        self.simulationNode = self.sourceNode.parent().createNode("dopnet", "SIMULATION")
        outputNode          = self.simulationNode.displayNode()

        gravityNode         = outputNode.createInputNode(0, "gravity", "gravity1")
        gravityNode.setParms(self.gravityParms)

        pyroSolverNode      = gravityNode.createInputNode(0, "merge").createInputNode(0, "pyrosolver::2.0")
        pyroSolverNode.setParms(self.pyroSolverSimulation)
        pyroSolverNode.setParms(self.pyroSolverCombustion)
        pyroSolverNode.setParms(self.pyroSolverShape)
        pyroSolverNode.setParms(self.pyroSolverAdvanced)

        smokeObjectNode     = pyroSolverNode.createInputNode(0, "smokeobject", "pyro")
        smokeObjectNode.setParms(self.pyroSmokeObject)

        resizeContainerNode = pyroSolverNode.createInputNode(1, "gasresizefluiddynamic", "resize_container")
        resizeContainerNode.setParms({"operator_path":self.sourceNode.path()})
        resizeContainerNode.setParms(self.resizeContainerParms)

        sourceVolumeNode    = pyroSolverNode.createInputNode(4, "merge", "merge2").createInputNode(0, "sourcevolume", "source_density_from_sphere")
        sourceVolumeNode.setParms({"source_path":self.sourceNode.displayNode().path()})
        sourceVolumeNode.setParms(self.sourceVolumeParms)
        self.simulationNode.layoutChildren()

    '''FUNC: CreateNodeInline
    nodeType: Type of node ("null", "merge")
    nodeName: Label of node ("AwesomeNull", "NeatSim")
    referenceNode: Reference SopNode to build off of. Still reference one even if not connecting.
    setDisplayFlag: Set the display flag (True/False)
    setRenderFlag: Set the render flag (True/False)
    connectToInput: Determines if node connects or is isolated


    '''
    def CreateNodeInline(self, nodeType="null", nodeName="null", referenceNode=None, setDisplayFlag=True, setRenderFlag=True, connectToInput=True, inputNumber=0):
        temp = referenceNode.parent().createNode(nodeType, nodeName)
        if connectToInput:
            temp.insertInput(inputNumber, referenceNode.parent().displayNode())
        temp.setDisplayFlag(setDisplayFlag)
        temp.setRenderFlag(setRenderFlag)
