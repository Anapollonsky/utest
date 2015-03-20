import telnetlib
import socket
import time
from interfaces.frame import Interactive_Frame
from decorators import command

class BCI_Frame(Interactive_Frame):
    interfacename = "bci"
    
    def establish_connection(self, address, username, password):
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
        return con

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
        time.sleep(.1)
        return self._connection.read_very_eager().decode('ascii')        

################################################################################
#################### Command functions
    @command(0, quiet=True)
    def username(self, username):
        """Used to set the connection username, if any."""
        self._username = username        

    @command(0, quiet=True)
    def password(self, password):
        """Used to set the connection password, if any."""
        self._password = password
    @command(0, quiet=True)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address
    
