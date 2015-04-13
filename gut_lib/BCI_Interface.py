import telnetlib
import socket
import time
import re
from Interface import Interactive_Interface

class BCI(Interactive_Interface):

########## Base Behavior Functions

    def connect(self, address, username, password):
        """ Connection procedure for bci."""
        try:
            con = telnetlib.Telnet(address, 7006, 10)
        except socket.timeout:
            return None
        con.expect(['ogin'.encode('ascii')])
        con.write(username.encode('ascii') + b"\n")
        con.expect(['assword'.encode('ascii')])
        con.write(password.encode('ascii') + b"\n")
        time.sleep(.2)        
        con.expect([b">"])
        self._connection = con
        self._address = address
        self._username = username
        self._password = password

    __init__ = connect
 
    def expect(self, array, timer = 10):
        """Wait for a message from an array, return either a capture and everything
        preceding it or None in the event of a timeout."""
        array = [array] if isinstance(array, str) else array
        results = self._connection.expect([x.encode('ascii') for x in array], timer)
        if results[0] == -1:
            return None
        else:
            return results[2].decode('ascii')

    def sendline(self, text):
        """Transmit a frame object's content to intended recipient."""
        self._connection.write(text.encode('ascii') + b"\n")
        self.expect(text)

    def capture(self):
        """Capture text without knowing what to 'expect'"""
        time.sleep(.3)
        return self._connection.read_very_eager().decode('ascii')        

    def close(self):
        self._connection.close()

########## Command functions
    def fpga_write(self, address, value):
        address = address if isinstance(address, str) else str(hex(address))
        value = value if isinstance(value, str) else str(hex(value))
        self.sendline("/pltf/txpath/fpgawrite " + address + " " + value)
        return self.expect("SUCCESS")

    def set_reference(self, ref):
        if ref == "EXT":
            val = 0x5000
        elif ref == "CPRI":
            val = 0x4000
        else:
            return None
        return self.fpga_write(0x206, val)

    def set_output(self, status):
        val = 0x4077 if status else 0x77
        self.fpga_write(0x0, val)
    
    def ensure_pll_lock(self, number):
        self.sendline("/pltf/txPath/pllStatus")
        return self.expect("ext synth " + str(number) + " is locked")

    def do_tx_play_waveform(self, filename):
        self.sendline("/pltf/bsp/loadfpgasram " + filename + " 3 0x0")
        self.fpga_write(0x18, 0x0)
        self.fpga_write(0x19, 0x0f1f) 
        self.fpga_write(0xc, 0xF00)
        self.fpga_write(0x1f, 0x0c24)
        self.fpga_write(0x1e, 0xffff)
        self.fpga_write(0x10, 0x2004)
        self.fpga_write(0x11, 0x2D34) # DDR Playback scale +3dB
        return self.fpga_write(0x0, 0x4077)

    def set_lo(self, device, freq):
        """ Frequency in KHz

        device mapping:
        chip - range from [0:3]
          0 - TX ROC0
          2 - RX ROC0
        freq    frequency to be set to LO
        i.e
                setFreq 1 2655000
                        Set TX LO to 2.655Ghz"""
        self.sendline("/pltf/txPath/setLoFreq " + str(device) + " " + str(freq))
        return self.expect("OK")
        
    def set_atten(self, device, value):
        """Device Listing:
        0  - ROC TX1 ATTN
        1  - ROC TX2 ATTN
        4  - ROC TX1 EXT ATTN
        5  - ROC TX2 EXT ATTN
        8  - ROC SRX0 ATTN
        10  - ROC RX1 ATTN :sets manual gain index
        11  - ROC RX2 ATTN :sets manual gain index
        """
        self.sendline("/pltf/txpath/setAttn " + str(device) + " " + str(value))
        return self.expect("OK")

    def set_tx_rf_switches(self, device, path):
        self.sendline("/pltf/txPath/setRfSwitches " + str(device) + " " + str(path))
        return self.expect("SUCCESS")

        
    def do_srx_capture(self, filename):
        self.fpga_write(0x204, 0x0)
        self.fpga_write(0xd, 0x40)
        self.fpga_write(0x12, 0x3)
        self.fpga_write(0x0, 0xc077)
        self.fpga_write(0x0, 0x4077)
        self.fpga_write(0x12, 0x0)
        self.sendline("/pltf/bsp/readfpgasram " + filename + " 12288000 2 0x01800000")
        return self.expect("reading fpga sram successful")

    def get_srx_power(self, device):
        self.sendline("/pltf/txPath/readSrxPower " + str(device))
        capture = self.expect("SUCCESS")
        return float(re.search('Srx power = (\-?\d+\.?\d+)', capture).group(1))

    def do_rx_capture(self, filename, rx):
        rx_value = 0x020 if rx == 1 else 0x120
        self.fpga_write(0x2a30, 0xf)
        self.fpga_write(0xd, rx_value)
        self.fpga_write(0x12, 0x3)
        self.fpga_write(0x0, 0x8077)
        self.fpga_write(0x0, 0x77)
        self.fpga_write(0x12, 0x0)
        self.sendline("/pltf/bsp/readfpgasram " + filename + " 6144000 2 0x01800000")
        return self.expect("reading fpga sram successful")

    # def do_test_tone(self):
    #     def get_gain(dbs):
    #     #  per carrier TX gain (before DUC): gain(dB)=20*log10(TX_GAIN/8192); 0x2000=unity, 0x2D34=3dB, 0x1000=-6dB
    #         return (10 ^ (dbs / 20)) * 8192

    #     def get_offset(khz):
    #     #  DUC NCO frequency:  14-bit 2s-complement, 10kHz step, +/-45MHz
    #     #   ex:  carrier1: +10MHz = 1000 = 0x3E8;  carrier2: -10MHz = -1000 = 0x3C18
    #         return hex(((abs(khz) ^ 0x3fff) + 1) & 0x3fff)
            
    #     #####################################################################
    #     #####  playback 2 test tones per diversity

    #     #####  force LMK to use 15.36 MHz test reference instead of recovered CPRI clock
    #     self.fpga_write(0x206, 0x5000)
    #     #####  DDR base addr (PS DDR) – need to have playback logic active, even though constant will replace pb data
    #     self.fpga_write(0x18, 0x0000)
    #     self.fpga_write(0x19, 0x0F1F)
    #     #####  clear alarms – be careful with these registers for a full radio!!!
    #     self.fpga_write(0x1F, 0xFFFF)
    #     self.fpga_write(0x1E, 0xFFFF)
    #     #####  enable test tone (chiprate playback before DUC.. data -> DC value)
    #     self.fpga_write(0x0C, 0x0001)
    #     #####  SDRAM1_MODE: bits(2:0)
    #     #####   0x1: TX_TDMA_INS (chip rate)
    #     self.fpga_write(0x10, 0x0001)
    #     #####  per carrier TX gain (before DUC): gain(dB)=20*log10(TX_GAIN/8192); 0x2000=unity, 0x2D34=3dB, 0x1000=-6dB
    #     #####   divAc1, divBc1, divAc2, divBc2, divCc1, divDc1, divCc2, divDc2
    #     self.fpga_write(0x1010, 0x1000)
    #     self.fpga_write(0x1011, 0x1000)
    #     self.fpga_write(0x1012, 0x1000)
    #     self.fpga_write(0x1013, 0x1000)
    #     self.fpga_write(0x1014, 0x1000)
    #     self.fpga_write(0x1015, 0x1000)
    #     self.fpga_write(0x1016, 0x1000)
    #     self.fpga_write(0x1017, 0x1000)
    #     #####  DUC NCO frequency:  14-bit 2s-complement, 10kHz step, +/-45MHz
    #     #####   ex:  carrier1: +10MHz = 1000 = 0x3E8;  carrier2: -10MHz = -1000 = 0x3C18
    #     self.fpga_write(0x1060, 0x03E8)
    #     self.fpga_write(0x1061, 0x3C18)
    #     #####  DUC carrier bandwidth bits(2:0):  2=5MHz, 3=10MHz, 5=20MHz
    #     self.fpga_write(0x1070, 0x2)
    #     self.fpga_write(0x1071, 0x2)
    #     #####  DEV_CTRL1: normal operation (0x77), turn on playback: 0x4077
    #     # self.fpga_write(0x0, 0x4077)
    #     #####  set TX attenuators to min attn
    #     # self.set_atten(4, 0)
    #     # self.set_atten(5, 0)


