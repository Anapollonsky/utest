from time import sleep
import re
from SCPI_Interface import SCPI

class N9020A(SCPI):
    __init__ = SCPI.connect

    def set_marker_mode(self, ind, mode):
        """Set marker mode. Ind is value 1-12, mode is one of 'POS', 'DELT', 'FIX', 'OFF'"""
        if ind in range(1, 13):
            return self.echo("CALC:MARK" + str(ind) + ":MODE " + mode.upper())
        else:
            return None

    def set_marker_axis(self, ind, axis, value):
        """ Set marker axis value """
        axis = axis.upper()
        axes = ['X','Y','Z']
        if axis in axes and ind in range(1, 13):
            return self.echo("CALC:MARK" + str(ind) + ":" + axis + " " + str(value))
        else:
            return None

    def set_freq(self, freq): 
        """ Permanently Set center frequency"""
        # self._connection.read_very_eager()
        return self.echo(":SENS:FREQ:CENT " + str(freq) + " hz")
        
    def set_external_gain(self, val):
        """Set Ext Gain to value in dB"""
        return self.echo("CORR:SA:GAIN " + val)
        
    def set_mech_atten(self, val):
        """Set mechanical attenuation to value in dB"""
        return self.echo("POW:ATT " + str(val))
        
    def set_ref_level(self, val):
        """Set reference level to value in dB"""
        return self.echo("DISPLAY:WINDOW:TRACE:Y:RLEVEL " + str(val))
        
    def set_detector(self, val = "AVER", trace = 1):
        """Set detector, such as RMS by default (AVER)"""
        return self.echo("DET:TRACE" + str(trace) + " " + val)
        
    def set_averaging_count(self, count):
        """Set averaging count"""
        return self.echo("CHP:AVERAGE:COUNT " + str(count))
        
    def set_integration_bandwidth(self, bandwidth):
        return self.echo(":SENS:CHP:BAND:INT " + str(bandwidth) + " hz")
        
    def set_continuous_sweep(self, val):
        """Set continuous sweep to on or off"""
        inc = "ON" if val else "OFF"
        return self.echo("INIT:CONT %s" % inc)
        
    def set_auto_align(self, val):
        inc = "ON" if val else "OFF"
        return self.echo("CAL:AUTO %s" % inc)
        
    def set_resolution_bandwidth(self, bw):
        return self.echo("CHP:BAND:RESOLUTION " + str(bw) + " hz")
 
    def set_mode(self, mode = "CHP"):
        """Set the mode to something, like "CHP" for channel power."""
        return self.echo(":INIT:" + mode)

    def set_span(self, freq):
        """Set MXA Span"""
        # return self.echo(":SENS:FREQ:SPAN" + str(freq) + " " + str(unit))
        return self.echo("CHP:FREQ:SPAN " + str(freq) + " HZ")
    
    def get_value_at_freq(self, freq, axis = 'Y', marker = 12):
        """Get value at frequency"""
        self.set_marker_mode(marker, 'POS')
        self.set_marker_axis(marker, 'X', str(freq) + " HZ")
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
            return self.echo("CALC:MARK" + str(ind) + ":" + axis + "?")
        else:
            return None

    def get_peaks(self, source = 1, threshold = 10, excursion = -200, sort = "FREQ"):
        """Provide list of Amplitude,Frequency pairs for given threshold and excursion"""
        return self.echo(":CALC:DATA" + str(source) + ":PEAK? " + str(excursion) + "," + str(threshold) + "," + str(sort))
  
    def get_chanpwr_psd(self):
        """Get the channel power and PSD."""
        self.sendline(":READ:CHP?")
        regex = "(\-?\d.*),(\-?\d.*)"
        capture = self.expect(regex, 20)
        return tuple(float(x)for x in re.search(regex, capture).groups()) 

    def get_external_gain(self):
        capture = self.echo(":CORR:SA:GAIN?")
        value = re.search("(\-?\d\S+)", capture).groups()[0]
        return int(float(value))
    
    def do_manual_alignment(self):
        self.sendline("CAL:EXP?")
        self.expect("0")

    def set_video_bandwidth(self, bw):
        return self.echo("CHP:BAND:VIDEO " + str(bw) + " HZ")
        
    def do_reset(self):
        return self.echo("*RST")
    
    def do_jeff_mxa_setup(self):
        self.do_reset()
        self.set_continuous_sweep(True)
        self.set_mech_atten(20)
        self.set_ref_level(10)
        self.set_detector("AVER")
        self.set_mode("CHP")
        self.sendline("CHP:FREQ:SYNT:AUTO ON")
        self.sendline("CHP:IF:GAIN:AUTO ON")
        self.set_averaging_count(500)
        self.set_integration_bandwidth(5e6)
        self.set_resolution_bandwidth(3e4)
        self.sendline("CHP:BAND:VIDEO:AUTO OFF")
        self.set_video_bandwidth(3e5)
        self.set_span(7.5e6) 
        self.set_auto_align(False)
        self.do_manual_alignment()
