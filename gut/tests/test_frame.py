import pytest
from interfaces.frame import Frame
from interfaces.frame import Interactive_Frame
from conman import Conman

basic = {"interface": "sh", "send": "ls /"}

conman = Conman(3)

def test_frame_composition(los, conman, interfacename):
    frame = conman.get_interface(interfacename)(los, conman)
    for member in los:
        assert str(member) in frame.args

test_frame_composition(basic, conman, "telnet")
