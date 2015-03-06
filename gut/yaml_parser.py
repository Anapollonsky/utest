import yaml
import re
import utils as ut
from frame import Frame

# Symbol table. Used to map yaml-file names to internal names, when necessary
sym = {}

def symbol_substitutions(input_string, symbols):
    """Perform substitutions in the string, replacing all 'values' from an external dictionary with the corresponding 'keys'."""
    outstr = str(input_string)
    for i, k in symbols.items():
        outstr = re.sub(k, i, outstr)
    return outstr

def parse_yaml(stream, conman):
    """Take a YAML stream and parse it in such a way that the upper-most dictionary is instead saved as a list, for sequential access."""
    substituted_string = symbol_substitutions(stream.read(), sym)
    yamlsplit = re.split("\n(?!\s)", substituted_string.strip())
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#']
    return yamlparse
