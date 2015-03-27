import yaml
import re
import utils as ut

## Due to the desire to access aliases globally, includes are parsed separately.




def parse_yaml(stream):
    return yaml.load(stream.read())

