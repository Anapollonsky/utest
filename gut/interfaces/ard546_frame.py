import time
import telnetlib
import socket
from frame import Frame
from decorators import command

class ARD546_Frame(Frame):
    interfacename = "ard546"    

    def establish_connection(self, address):
        """ Connection procedure for ard546."""
        try:
            con = telnetlib.Telnet(address, 1307, 10)
        except socket.timeout:
            return None
        time.sleep(.2)
        return con

    def send_frame(self):
        """Transmit a frame object's content to intended recipient."""
        self._connection.write(self.send["content"] + "\n")

    def expect_message(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""                
        results = self._connection.expect(array, timer)
        if results[0] == -1:
            return (None, True) # Return no capture, timeout
        else:
            return (results[2], False) # Return capture, no timeout        

    def capture_message(self):
        """Try to capture text without an "expect" clause."""
        time.sleep(.4)
        return self._connection.read_very_eager()

################################################################################
#################### Command functions

    @command(0)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address

