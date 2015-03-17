import time
import telnetlib
import socket
from interfaces.scpi_frame import scpi_Frame
from decorators import command

class MXA_Frame(scpi_Frame):
    interfacename = "mxa"
    
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
        """Permanently Set center frequency, in MHz by default"""
        self._connection.write((":SENS:FREQ:CENT " + str(freq) + " " + str(unit) + "\n").encode('ascii'))
