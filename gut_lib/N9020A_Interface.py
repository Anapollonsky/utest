from time import sleep
import re
from SCPI_Interface import SCPI

class N9020A(SCPI):

    __init__ = SCPI.connect

    def set_marker_mode(self, ind, mode):
        """Set marker mode. Ind is value 1-12, mode is one of 'POS', 'DELT', 'FIX', 'OFF'"""
        if ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":MODE " + mode.upper())
            return self.capture()
        else:
            return None

    def set_marker_axis(self, ind, axis, value):
        """ Set marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":" + axis + " " + str(value))
            return self.capture()
        else:
            return None

    def set_freq(self, freq, unit="MHz"):
        """ Permanently Set center frequency, in MHz by default """
        # self._connection.read_very_eager()
        self.sendline(":SENS:FREQ:CENT " + str(freq) + " " + str(unit))
        return self.capture()

    def set_mech_atten(self, val):
        """Set mechanical attenuation to value in dB"""
        self.sendline("POW:ATT " + str(val))
        return self.capture()

    def set_ref_level(self, val):
        """Set reference level to value in dB"""
        self.sendline("DISPLAY:WINDOW:TRACE:Y:RLEVEL " + str(val))
        return self.capture()

    def set_detector(self, val = "AVER", trace = 1):
        """Set detector, such as RMS by default (AVER)"""
        self.sendline("DET:TRACE" + str(trace) + " " + val)
        return self.capture()

    def set_averaging_count(self, count):
        """Set averaging count"""
        self.sendline("CHP:AVERAGE:COUNT " + str(count))
        return self.capture()

    def set_integration_bandwidth(self, bandwidth, unit):
        self.sendline(":SENS:CHP:BAND:INT " + str(bandwidth) + " " + str(unit))
        return self.capture()

    def set_continuous_sweep(self, val):
        """Set continuous sweep to on or off"""
        inc = "ON" if val else "OFF"
        self.sendline("INIT:CONT %s" % inc)
        return self.capture()

    def set_auto_align(self, val):
        inc = "ON" if val else "OFF"
        self.sendline("CAL:AUTO %s" % inc)
        return self.capture()

    def set_resolution_bandwidth(self, bw, unit="KHZ"):
        self.sendline("CHP:BAND:RESOLUTION " + str(bw) + " " + unit)
        return self.capture()
 
    def set_mode(self, mode = "CHP"):
        """Set the mode to something, like "CHP" for channel power."""
        self.sendline(":INIT:" + mode)
        return self.capture()

    def set_span(self, freq, unit="MHz"):
        """Set MXA Span"""
        # self.sendline(":SENS:FREQ:SPAN" + str(freq) + " " + str(unit))
        self.sendline("CHP:FREQ:SPAN " + str(freq) + " " + unit)
        return self.capture()
    
    def get_value_at_freq(self, freq, axis = 'Y', marker = 12, unit="MHz"):
        """Get value at frequency"""
        self.set_marker_mode(marker, 'POS')
        self.set_marker_axis(marker, 'X', str(freq) + " " + str(unit))
        self.capture()
        capture = self.get_marker_axis_value(marker, axis)
        self.set_marker_mode(marker, 'OFF')
        self.capture()
        return capture

    def get_marker_axis_value(self, ind, axis):
        """ Get marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            self.sendline("CALC:MARK" + str(ind) + ":" + axis + "?")
            return self.capture()
        else:
            return None

    def get_peaks(self, source = 1, threshold = 10, excursion = -200, sort = "FREQ"):
        """Provide list of Amplitude,Frequency pairs for given threshold and excursion"""
        self.sendline(":CALC:DATA" + str(source) + ":PEAK? " + str(excursion) + "," + str(threshold) + "," + str(sort))
        sleep(1)
        return self.capture()
  
    def get_chanpwr_psd(self):
        """Get the channel power and PSD."""
        self.sendline(":READ:CHP?")
        sleep(4)
        capture = self.capture()
        return tuple(float(x)for x in re.search("(\-?\d.*),(\-?\d.*)", capture).groups()) 

    def do_manual_alignment(self):
        self.sendline("CAL:EXP?")
        sleep(20)
        return self.capture()

    def do_reset(self):
        self.sendline("*RST")
        return self.capture()
    
    def do_jeff_mxa_setup(self):
        self.do_reset()
        self.set_continuous_sweep(True)
        self.set_mech_atten(20)
        self.set_ref_level(10)
        self.set_detector("AVER")
        self.set_mode("CHP")
        self.set_averaging_count(300)
        self.set_integration_bandwidth(5, "MHz")
        self.set_resolution_bandwidth(30, "KHz")
        self.sendline("CHP:BAND:VIDEO:AUTO ON")
        self.set_span(7.5, "MHz")
        self.set_auto_align(False)
        self.do_manual_alignment()
