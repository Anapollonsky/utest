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
        time.sleep(.8)
        con.read_very_eager() 
        return con
    
################################################################################
#################### Command functions

    @command(3)
    def set_output(self, state):
        """Set output to 1/on or 0/off"""
        states = ["OFF", "ON"]
        if state == 0:
            state = "OFF"
        elif state == 1:
            state = "ON"
        if state.upper() in states:
            state = state.upper()
        self._connection.read_very_eager()
        self.send_string("OUTPUT:STATE " + str(state))
        time.sleep(.4)

    @command(4)
    def get_output(self):
        """Get output voltage"""
        self._connection.read_very_eager()
        self.send_string("OUTPUT:STATE?")
        time.sleep(.4)

    @command(3)
    def set_volt(self, volt):
        """Set output voltage"""
        self._connection.read_very_eager()
        self.send_string("VOLT " + str(volt))
        time.sleep(.4)

    @command(4)
    def get_volt(self):
        """Get output voltage"""
        self._connection.read_very_eager()
        self.send_string("VOLT?")
        time.sleep(.4)
        
    @command(3)
    def set_current_limit(self, limit):
        """Set current limit, in amps"""
        self._connection.read_very_eager() 
        self.send_string("CURR:LIM " + str(limit))
        time.sleep(.4)

    @command(4)
    def get_current_limit(self):
        """Get current limit, in amps"""
        self._connection.read_very_eager() 
        self.send_string("CURR:LIM?")
        time.sleep(.4)
