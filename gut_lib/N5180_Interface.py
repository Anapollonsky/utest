from time import sleep
import telnetlib
import socket
from SCPI_Interface import SCPI

class N5180(SCPI):
    __init__ = SCPI.connect

################################################################################
#################### Command functions

    def set_output(self, state):
        """Set output to 1/on or 0/off"""
        state = "ON" if state else "OFF"
        self.echo("OUTPUT:STATE " + str(state))

    def set_freq(self, freq):
        """Permanently set output center frequency, in MHz by default"""
        self.sendline(":FREQ:MODE CW")
        self.capture()
        self.echo(":FREQ:CW " + str(freq) + " HZ")

    def get_freq(self):
        """Get output center frequency"""
        self.echo(":FREQ:CW?")

    def set_power(self, power):
        """ Set output power """
        self.echo(":POW:AMPL " + str(power) + " W")

    def get_power(self):
        """ Get output power """
        self.echo(":POW:AMPL?")
