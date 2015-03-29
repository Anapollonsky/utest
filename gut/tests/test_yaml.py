import yaml
from conman import Conman
import yaml_parser as pa
from copy import deepcopy
from nose import *

class TestYamlParse:

    def setup(self):
        self.conman = Conman(3)

    def test_yaml_1(self):
        filename = 'yamls/shtest1.yml'
        pa.init(self.conman, filename)
        dos = pa.parse_yaml(self.conman, open(filename).read())["do"]
        print(dos)
        assert dos == [{"type": "command",
                        "interface": "shell",
                        "send": "ls /",
                        "print_response": None},
                       {"type": "command",
                        "interface": "shell",
                        "send": "pwd",
                        "print_response": None},
                       {"type": "include",
                        "include": "shtest2.yml"}] 
        
