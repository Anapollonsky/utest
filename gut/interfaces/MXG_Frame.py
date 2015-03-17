import time
import telnetlib
import socket
from interfaces.scpi_frame import scpi_Frame
from decorators import command

class MXG_Frame(scpi_Frame):
    interfacename = "mxg"
    
    def establish_connection(self, address):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 5023, 10)
        except socket.timeout:
            return None
        time.sleep(.2)
        return con

################################################################################
#################### Command functions

    @command(3) 
    def center_freq(self, freq, unit="MHz"):
        """Permanently Set output center frequency, in MHz by default"""
        self.send_string(":FREQ:MODE CW")
        time.sleep(.1)
        self._connection.read_very_eager()        
        self.send_string(":FREQ:CW " + str(freq) + " " + str(unit))

