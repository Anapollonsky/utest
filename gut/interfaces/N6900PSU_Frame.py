import time
import telnetlib
import socket
from interfaces.scpi_frame import scpi_Frame
from decorators import command

class N6900_Frame(scpi_Frame):
    interfacename = "n6900"    

    def establish_connection(self, address):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 5024, 10)
        except socket.timeout:
            return None
        time.sleep(.2)
        return con

################################################################################
#################### Command functions

    @command(3)        
    def set_output(self, state):
        """Set output to 1/on or 0/off"""
        states = [OFF, ON]
        if state == 0:
            state = "OFF"
        elif state == 1:
            state = "ON"
        if state.upper() in states:
            state = state.upper()
        self._connection.write(("OUTPUT:STATE " + str(state) + "\n").encode('ascii'))


    @command(3)        
    def set_volt(self, volt):
        """Set output voltage"""
        self._connection.write(("VOLT " + str(volt) + "\n").encode('ascii'))

