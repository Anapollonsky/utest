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

    def send_string(self, string):
        """ Format a string for proper sendoff. """
        self._connection.write((string + "\n").encode('ascii'))
    
    def marker_mode(ind, mode):
        """Set marker mode. Ind is value 1-12, mode is one of 'POS', 'DELT', 'FIX', 'OFF'"""
        if ind in range(1, 13):
            self.end_string("CALC:MARK" + str(ind) + ":MODE " + mode.upper())
        else:
            self.conman.ferror("Invalid parameters passed to " + __func__ ": " + str(ind)+ " | " + str(mode))

    def marker_axis_set(ind, axis, value)
        """ Set marker axis value """
        axes = ['x','y','z']
        if axis in axes and ind in range(1, 13):
            self.send_string("CALC:MARK" + str(ind) + ":" + axis.upper() + " " + value) 
        else:
            self.conman.ferror("Invalid parameters passed to " + __func__ ": " + str(ind)+ " | " + str(axis))

    def marker_axis_get(ind, axis)
        """ Get marker axis value """
        axes = ['x','y','z']
        if axis in axes and ind in range(1, 13):
            self.send_string("CALC:MARK" + str(ind) + ":" + axis.upper() + "?") 
        else:
            self.conman.ferror("Invalid parameters passed to " + __func__ ": " + str(ind)+ " | " + str(axis))
            
        
################################################################################
#################### Command functions

    @command(3)        
    def center_freq(self, freq, unit="MHz"):
        """Permanently Set center frequency, in MHz by default. Must be set in vicinity of"""
        self.send_string(":SENS:FREQ:CENT " + str(freq) + " " + str(unit))

    @command(4)
    def send_val_freq(self, freq, axis = 'y', marker = 12):
        """Get value at frequency"""
        marker_axis_set(marker, 'x', freq)
        marker_axis_get(marker, axis)

    @command(4)
    def send_find_peaks(self, source = 1, threshold = 10, excursion = -200, sort = "FREQ"):
        """Provide list of Amplitude,Frequency pairs for given threshold and excurion"""
        self.end_string(":CALC:DATA" + str(source) + ":PEAK? " + excursion + "," + threshold + "," + sort)        

    
