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
        """Wait for a message from an array, return either a capture or a timeout."""
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
        """Try to capture text without an "expect" clause."""
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

    def ensure_pll_lock(self, number):
        self.sendline("/pltf/txPath/pllStatus")
        return self.expect("ext synth " + str(number) + " is locked")

    def tx_load_waveform(self, filename):
        self.sendline("/pltf/bsp/loadfpgasram " + filename + " 3 0x0")
        return self.expect("filename")

    def tx_play_waveform(self):
        self.fpga_write(0x18, 0x0)
        self.fpga_write(0xc, 0xF00)
        self.fpga_write(0x1f, 0x0c24)
        self.fpga_write(0x1e, 0xffff)
        self.fpga_write(0x10, 0x2004)
        self.fpga_write(0x11, 0x2D34) # DDR Playback scale +3dB
        return self.fpga_write(0x0, 0x4077)

    def tx_set_lo(self, device, freq):
        """ Frequency in KHz """
        self.sendline("/pltf/txPath/setLoFreq " + str(device) + " " + str(freq))
        return self.expect("OK")
        
    def tx_set_atten(self, device, value):
        self.sendline("/pltf/txpath/setAttn " + str(device) + " " + str(value))
        return self.expect("OK")

    def tx_set_rf_switches(self, device, path):
        self.sendline("/pltf/txPath/setRfSwitches " + str(device) + " " + str(path))
        return self.expect("SUCCESS")
        
    def srx_capture(self, filename):
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
