from time import sleep
import telnetlib
import socket
import re
from SCPI_Interface import SCPI

class N9020A(SCPI):

    __init__ = SCPI.connect

    def marker_mode(self, ind, mode):
        """Set marker mode. Ind is value 1-12, mode is one of 'POS', 'DELT', 'FIX', 'OFF'"""
        if ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":MODE " + mode.upper())
            sleep(.3)
            return self.capture()
        else:
            return None

    def marker_axis_set(self, ind, axis, value):
        """ Set marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":" + axis + " " + str(value))
            sleep(.1)
            return self.capture()
        else:
            return None
        
    def marker_axis_get(self, ind, axis):
        """ Get marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":" + axis + "?")
            sleep(.1)
            return self.capture()
        else:
            return None

    def set_freq(self, freq, unit="MHz"):
        """ Permanently Set center frequency, in MHz by default """
        # self._connection.read_very_eager()
        self.sendline(":SENS:FREQ:CENT " + str(freq) + " " + str(unit))
        return self.capture()

    def get_val_freq(self, freq, axis = 'Y', marker = 12, unit="MHz"):
        """Get value at frequency"""
        self.marker_mode(marker, 'POS')
        self.marker_axis_set(marker, 'X', str(freq) + " " + str(unit))
        sleep(.2)
        self.capture()
        capture = self.marker_axis_get(marker, axis)
        self.marker_mode(marker, 'OFF')
        self.capture()
        return capture

    def find_peaks(self, source = 1, threshold = 10, excursion = -200, sort = "FREQ"):
        """Provide list of Amplitude,Frequency pairs for given threshold and excursion"""
        # self._connection.read_very_eager()
        self.sendline(":CALC:DATA" + str(source) + ":PEAK? " + str(excursion) + "," + str(threshold) + "," + str(sort))
        return self.capture()

    def set_mode(self, mode = "CHP"):
        """Set the mode to something, like "CHP" for channel power."""
        self.sendline(":INIT:" + mode)
        return self.capture()

    def set_span(self, freq, unit="MHz"):
        self.sendline(":SENS:FREQ:SPAN" + str(freq) + " " + str(unit))
        return self.capture()

    def get_channel_power(self, center, bandwidth, cunit="MHz", bunit="MHz"):
        """Get the channel power, performing all intermediary legwork."""
        self.sendline(":INIT:CHP")
        sleep(.2)
        self.sendline(":SENS:FREQ:CENT " + str(center) + " " + str(cunit))
        sleep(.2)
        self.sendline(":SENS:FREQ:SPAN " + str(bandwidth) + " " + str(bunit))
        sleep(.2)
        print("test")
        self.sendline(":SENS:CHP:BAND:INT " + str(bandwidth) + " " + str(bunit))
        sleep(.2)
        self._connection.read_very_eager()
        sleep(.2)
        self.sendline(":READ:CHP?")
        sleep(2)
        capture = self.capture()
        return float(re.search("(\-?\d.*),", capture).groups()[0]) 
