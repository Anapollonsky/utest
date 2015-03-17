import time
import telnetlib
import socket
from interfaces.frame import Interactive_Frame
from decorators import command

class scpi_Frame(Interactive_Frame):


    def send_frame(self):
        """Transmit a frame object's content to intended recipient."""
        self._connection.write(self._send.encode('ascii') + b"\n")        

    def expect_message(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""
        results = self._connection.expect([x.encode('ascii') for x in array], timer)
        if results[0] == -1:
            return (None, True) # Return no capture, timeout
        else:
            return (results[2].decode('ascii'), False) # Return capture, no timeout

    def capture_message(self):
        """Try to capture text without an "expect" clause."""
        time.sleep(.3)
        return self._connection.read_very_eager().decode('ascii')        
    
################################################################################
#################### Command functions

    @command(0, quiet=True)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address
 
