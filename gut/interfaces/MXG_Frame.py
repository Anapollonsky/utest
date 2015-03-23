import time
import telnetlib
import socket
from interfaces.scpi_frame import scpi_Frame
from decorators import command

class MXG_Frame(scpi_Frame):
    interfacename = "n5180mxg"

    def establish_connection(self, address):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 5023, 10)
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

    @command(3)
    def set_freq(self, freq, unit="MHz"):
        """Permanently set output center frequency, in MHz by default"""
        self.send_string(":FREQ:MODE CW")
        time.sleep(.1)
        self._connection.read_very_eager()
        self.send_string(":FREQ:CW " + str(freq) + " " + str(unit))

    @command(3)
    def get_freq(self):
        """Get output center frequency"""
        self._connection.read_very_eager()
        self.send_string(":FREQ:CW?")

    @command(3)
    def set_power(self, power, unit="W"):
        """ Set output power """
        self._connection.read_very_eager()
        self.send_string(":POW:AMPL " + str(power) + " " + str(unit))
        time.sleep(.4)

    @command(3)
    def get_power(self):
        """ Get output power """
        self.send_string(":POW:AMPL?")
