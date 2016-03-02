import RealTimeVFXToolset
reload(RealTimeVFXToolset)

def init(nodes):
    print 'Processing Keyframes'
    RealTimeVFXToolset.keyframeReducer(nodes)
    print 'Processing Complete!'
