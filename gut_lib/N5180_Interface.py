from time import sleep
import telnetlib
import socket
from SCPI_Interface import SCPI

class N5180(SCPI):

    # def __init__(self, address):
    #     """ Connection procedure for remote shell."""
    #     try:
    #         con = telnetlib.Telnet(address, 5024, 10)
    #     except socket.timeout:
    #         return None
    #     sleep(.8)
    #     con.read_very_eager()
    #     self._address = address
    #     self._connection = con

    __init__ = SCPI.connect

################################################################################
#################### Command functions

    def set_output(self, state):
        """Set output to 1/on or 0/off"""
        state = "ON" if state else "OFF"
        return self.echo("OUTPUT:STATE " + str(state))

    def set_freq(self, freq):
        """Permanently set output center frequency, in MHz by default"""
        # self.echo(":FREQ:MODE CW")
        return self.echo(":FREQ:CW " + str(freq) + " HZ")

    def get_freq(self):
        """Get output center frequency"""
        return self.echo(":FREQ:CW?")

    def set_power(self, power):
        """ Set output power """
        return self.echo(":POW:AMPL " + str(power) + " DB")

    def get_power(self):
        """ Get output power """
        return self.echo(":POW:AMPL?")
