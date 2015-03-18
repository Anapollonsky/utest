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
        time.sleep(.8)
        con.read_very_eager() 
        return con

################################################################################
#################### Helper Functions

    def marker_mode(self, ind, mode):
        """Set marker mode. Ind is value 1-12, mode is one of 'POS', 'DELT', 'FIX', 'OFF'"""
        if ind in range(1, 13):
            self.send_string("CALC:MARK" + str(ind) + ":MODE " + mode.upper())
            time.sleep(.3)
        else:
            self.conman.ferror("Invalid parameters passed to marker_mode: " + str(ind)+ " | " + str(mode))

    def marker_axis_set(self, ind, axis, value):
        """ Set marker axis value """
        axis = axis.upper()        
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.send_string("CALC:MARK" + str(ind) + ":" + axis + " " + str(value))
            time.sleep(.1)
        else:
            self.conman.ferror("Invalid parameters passed to marker_axis_set: " + str(ind)+ " | " + str(axis))

    def marker_axis_get(self, ind, axis):
        """ Get marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.send_string("CALC:MARK" + str(ind) + ":" + axis + "?")
            time.sleep(.1) 
        else:
            self.conman.ferror("Invalid parameters passed to marker_axis_get: " + str(ind)+ " | " + str(axis))

################################################################################
#################### Command functions

    @command(3)        
    def center_freq(self, freq, unit="MHz"):
        """ Permanently Set center frequency, in MHz by default """
        self._connection.read_very_eager()
        time.sleep(.2)
        self.send_string(":SENS:FREQ:CENT " + str(freq) + " " + str(unit))


    @command(4)
    def val_freq(self, freq, axis = 'Y', marker = 12, unit="MHz"):
        """Get value at frequency"""
        self.marker_mode(marker, 'POS')
        self.marker_axis_set(marker, 'X', str(freq) + " " + str(unit))
        time.sleep(.2)
        self._connection.read_very_eager()
        self.marker_axis_get(marker, axis)
        self.marker_mode(marker, 'OFF')

    @command(4)
    def find_peaks(self, source = 1, threshold = 10, excursion = -200, sort = "FREQ"):
        """Provide list of Amplitude,Frequency pairs for given threshold and excursion"""
        self._connection.read_very_eager()
        time.sleep(.2)
        self.send_string(":CALC:DATA" + str(source) + ":PEAK? " + str(excursion) + "," + str(threshold) + "," + str(sort))

