import yaml
import re
import utils as ut
from gut_frame import Frame

# Symbol table
sym = {"sh": "shcommand", 
       "bci":"bcicommand",
       "ard546":"ard546command",
       "inc":"include",
       "glo":"global",
       "var":"variables",
       "rrej":"reject-regex",
       "rej":"reject",
       "expr":"expect-regex",
       "exp":"expect",
       "send":"send",
       "wait":"wait",
       "tout":"timeout"}

def symbol_substitutions(instr, symbols):
    """Perform substitutions in the string, replacing all 'values' from an external dictionary with the corresponding 'keys'."""
    outstr = str(instr)
    for i, k in symbols.items():
        outstr = re.sub(k, i, outstr)
    return outstr

def parse_yaml_file(thefile):
    """Take a YAML file and parse it in such a way that the upper-most dictionary is instead saved as a list, for sequential access."""
    try:
        infile = open(thefile, 'r')
    except IOError:
        ut.notify("fatalerror", "Failed to open file " + thefile + ", exiting")

    substituted_string = symbol_substitutions(infile.read(), sym)
    yamlsplit = re.split("\n(?!\s)", substituted_string.strip())
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#']
    return yamlparse

def frameFromLos(conman, los):
    """Generate a frame from a dictionary of local settings."""
    frame = Frame(los["send"])
    frame.expect = los["exp"]
    frame.expect_regex = los["expr"]
    frame.reject = los["rej"]
    frame.reject_regex = los["rrej"]
    frame.wait = los["wait"]
    frame.timeout = los["tout"]
    frame.connection = conman.openconnection(los["interface"], los["board"])
    return frame
