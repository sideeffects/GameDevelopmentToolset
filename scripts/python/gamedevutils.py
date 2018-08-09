import os
import requests
import hou

home = os.environ["HOUDINI_USER_PREF_DIR"]
config = os.path.join(home, "hcommon.pref")

GA_TRACKING_ID = "UA-2947225-8"


def can_send_anonymous_stats():
    can_share = False

    f = open(config, "r")
    for line in f.readlines():
        if line.startswith("sendAnonymousStats"):
            if line.strip().strip(";").split(":=")[1].strip() == "1":
                can_share = True
            break
    f.close()

    override = os.getenv("HOUDINI_ANONYMOUS_STATISTICS", 1)
    if int(override) == 0:
        can_share = False

    return can_share


def track_event(category, action, label=None, value=0):

    data = {
        'v': '1',  # API Version.
        'tid': GA_TRACKING_ID,  # Tracking ID / Property ID.
        # Anonymous Client Identifier. Ideally, this should be a UUID that
        # is associated with particular user, device, or browser instance.
        'cid': '555',
        't': 'event',  # Event hit type.
        'ec': category,  # Event category.
        'ea': action,  # Event action.
        'el': label,  # Event label.
        'ev': value,  # Event value, must be an integer
    }

    try:
        response = requests.post(
            'http://www.google-analytics.com/collect', data=data, timeout=0.1)

    except:
        pass


def like_node(node):
    if can_send_anonymous_stats():
        track_event("Like Events", "liked node", str(node.type().name()))
        hou.ui.displayMessage("Thanks!\n We're glad you like using this tool.\n"
                              " Letting us know will help us prioritize which tools get focused on. ")


def send_on_create_analytics(node):
    if can_send_anonymous_stats():
        track_event("Node Created", str(node.type().name()), str(node.type().definition().version()))