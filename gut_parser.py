import yaml
import re
import gut_utils as ut
from gut_frame import Frame

# Symbol table. Used to map yaml-file names to internal names, when necessary
sym = {"sh": "shcommand", 
       "bci":"bcicommand",
       "ard546":"ard546command",
       "inc":"include",
       "glo":"global",
       "var":"variables",
       "reject_regex":"reject-regex",
       "reject":"reject",
       "expect_regex":"expect-regex",
       "expect":"expect",
       "wait-_after":"wait-after",
       "wait_before":"wait-before",
       "wait_time":"wait-time",
       "var_in_dict":"dict",
       "send_variable_replace":"vars",
       "store_regex":"store-regex",
       "check_regex":"check-regex"}

def symbol_substitutions(input_string, symbols):
    """Perform substitutions in the string, replacing all 'values' from an external dictionary with the corresponding 'keys'."""
    outstr = str(input_string)
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
