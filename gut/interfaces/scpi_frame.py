import time
import telnetlib
import socket
from frame import Interactive_Frame
from decorators import command

class scpi_Frame(Interactive_Frame):
    
################################################################################
#################### Command functions

    @command(0, quiet=True)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address
 
