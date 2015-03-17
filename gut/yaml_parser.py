import yaml
import re
import utils as ut

def parse_yaml(stream, conman):
    """Take a YAML stream and parse it in such a way that the upper-most dictionary is instead saved as a list, for sequential access."""
    yamlsplit = re.split("\n(?!\s)", stream.read().strip()) # Split into sequential dictionaries
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#'] # Parse dictionaries
    return yamlparse
