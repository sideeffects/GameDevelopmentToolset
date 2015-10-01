import imp
import os.path
import sys

from tests import Test

niftoaster = imp.load_module(
    "niftoaster",
    *imp.find_module("niftoaster", [os.path.join("scripts", "nif")]))

def call_niftoaster(*args):
    oldargv = sys.argv[:]
    # -j1 to disable multithreading (makes various things impossible)
    sys.argv = ["niftoaster.py", "-j1"] + list(args)
    toaster = niftoaster.NifToaster()
    toaster.cli()
    sys.argv = oldargv
    return toaster
