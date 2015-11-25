import hou

class BillowySmoke():
    sourceNode = None

    def __init__(self, parent=None):
        self.CommandStack()

    def CommandStack(self):
        if self.CheckForSource():
            print self.sourceNode
            self.GenerateInitialLayout()
        else:
            print "Error! See Above."

    def CheckForSource(self):
        self.sourceNode = hou.selectedNodes()

        if len(self.sourceNode) > 1:
            return False
        elif len(self.sourceNode) < 1:
            return False
        else:
            self.sourceNode = self.sourceNode[0]
            return True

    def GenerateInitialLayout(self):
        print "Generating initial layout"
