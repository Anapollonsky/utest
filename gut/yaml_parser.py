import yaml
import re
import utils as ut

## Due to the desire to access aliases globally, includes are parsed separately.

def init(conman, filename):
    try:
        infile = open(filename, 'r')
    except IOError:
        conman.ferror("Failed to open file " + filename + ", exiting")
    conman.global_yaml = extract_global(infile.read())
    
def extract_global(yamlstring):
    match_global = "(global:.*?)(?:\n\S|$)" # Match global, blah, and either fileend or \n\S
    global_match = re.search(match_global, yamlstring, flags=re.DOTALL)
    if global_match:
        return global_match.groups()[0].strip() + "\n"
    else:
        return ""

def parse_yaml(conman, input_string):
    return yaml.load(input_string)

 
