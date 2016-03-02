import re
import hou

def nodeSelectionValid(nodes = []):
    '''nodeSelectionValid
    Simple check to see if node list is valid.
    return bool
    '''
    if len(nodes) == 0:
        print 'No nodes detected!'
        return False
    return True

def nodeSelectionMatchParm(nodes = [], parm = 'soppath'):
    '''nodeSelectionMatchParm
    Checks all the listed nodes for a single parameter (ex. 'soppath', 'tx', etc).
    Designed to make sure all nodes match.
    '''
    for node in nodes:
        if node.parm(parm):
            continue
        else:
            print '{} does not contain parameter: {}'.format(node, parm)
            return False
    return True

def nodeSelectionMatchType(nodes = [], type = 'rbdpackedobject'):
    '''nodeSelectionMatchType
    Checks all the listed nodes match the type.
    '''
    for node in nodes:
        if node.type().name() == type:
            continue
        else:
            print '{} does not match the type: {}'.format(node, type)
            return False
    return True

def findNonDOPGeometry(nodes, searchParameter, skipParameter):
    '''
    This function searches for a 'soppath' parameter to find the original SOP
    network. Then it crawls through each input[0] to find the first node that
    doesn't have the 'dopobject' attribute (basically skipping the dopimport).

    for each in nodes:
        find the parameter that contains a reference to another network
        while skipParameter still exists
            crawl through each input[0] until it doesn't exist
    return resulting geometry nodes
    '''

    displayNodes = []

    for node in nodes:
        if searchParameter:
            temp = node.parm(searchParameter).unexpandedString()
            if 'opinputpath' in temp:
                temp = temp.split('"')[1::2][0]
            temp = node.node(temp)
        else:
            temp = node

        referenceFound = False
        while(referenceFound == False):
            if(temp.geometry().findPrimAttrib(skipParameter) != None):
                temp = temp.inputs()[0]
            elif(temp.geometry() == None):
                temp = temp.inputs()[0]
            else:
                displayNodes.append(temp)
                break

    return displayNodes

def indexAttributeEntries(nodes, attributeString):
    '''
    Calculates the number of entries for a given attribute per node.
    Returns a nested list: [geometryNumber[attributeEntry]]
    '''
    numberOfHits = []

    for node in nodes:
        objGeometry = node.geometry()
        listPieces = []

        if objGeometry.findPointAttrib(attributeString):
            listPieces = objGeometry.findPointAttrib(attributeString).strings()
        elif objGeometry.findPrimAttrib(attributeString):
            listPieces = objGeometry.findPrimAttrib(attributeString).strings()
        numberOfHits.append(len(listPieces))
    return numberOfHits

def deleteKeyframes(nodes, startFrame, endFrame, step, parameters = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']):
    '''
    For each node, cycle through the frames with a certain step size and
    delete the listed parameter keyframe.
    '''
    print 'Processing Start.'
    for node in nodes:
        print 'Processing Node: ' + node.name()
        for frame in range(startFrame, endFrame, step):
            for PARM in parameters:
                node.parm(PARM).deleteKeyframeAtFrame(frame)
    print 'Processing Complete!'

def checkPointAttributeNaming(nodes, attribute):
    '''checkCountingNamingConvention
    For each node, search for the attribute, make sure the string is in each
    entry, and then make sure that the order matches.
    '''

    for node in nodes:
        if node.geometry().findPointAttrib(attribute) == None:
            print 'Error. {} doesn\'t exist as a point attribute!'.format(attribute)
            return None

        entries = node.geometry().findPointAttrib(attribute).strings()
        textCheck = ""

        for idx, entry in enumerate(entries):
            attributeText, attributeNumber, blank = re.split('(\d+)', entry)

            if idx == 0:
                textCheck = attributeText

            if attributeText != textCheck:
                print "Error! Name inconsistency with " + entry
                return None

            if int(attributeNumber) != idx:
                print "Error! Attribute counting inconsistency at " + entry
                return None

        return True

def keyframeReducer(nodes,
                    parms = [],
                    startFrame = int(hou.expandString('$RFSTART')),
                    endFrame = int(hou.expandString('$RFEND')),
                    tolerance = 0.0001):
    '''keyframeReducer
    For each node, look for the specified parameters during the frame range. If the difference between the current and next frame is less than the tolerance, remove the keyframe.

    If the parm list is empty, it will search though ALL parameters for the specified node. This will take a long time if you have a lot of nodes.
    '''

    print 'Processing Keyframes'
    originalKeyframes = 0
    deletedKeyframes = 0
    modified = False

    for node in nodes:
        for frame in range(startFrame, endFrame+1):
            if not parms:
                temp = node.parms()
                for parm in temp:
                    parms.append(parm.name())
            for parm in parms:
                if node.parm(parm).keyframesInRange(frame, frame):
                    originalKeyframes += 1
                    if abs(node.parm(parm).evalAsFloatAtFrame(frame+1) - node.parm(parm).evalAsFloatAtFrame(frame)) < tolerance:
                        if not modified:
                            modified = True
                        deletedKeyframes += 1
                        tempValue = node.parm(parm).eval()
                        node.parm(parm).deleteKeyframeAtFrame(frame)
                        node.parm(parm).set(tempValue)

    if modified:
        print 'Initial Frames: {}\nDeleted Frames: {}\nPercent Removed: {}%'.format(originalKeyframes, deletedKeyframes, deletedKeyframes/float(originalKeyframes)*100)
    else:
        print 'No Keyframes Removed'
    print 'Keyframe Processing Complete'
