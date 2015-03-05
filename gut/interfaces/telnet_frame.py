import time
import telnetlib
import socket
from frame import Frame

class telnet_Frame(Frame):
    interfacename = "telnet"    

    def establish_connection(self, address, username, password):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 23, 10)
        except socket.timeout:
            return None
        con.expect(["ogin"])
        con.write(username + "\n")
        con.expect(["assword"])
        con.write(password + "\n")
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

    def username(self, username):
        """Used to set the connection username, if any."""
        self._username = username        
    username.priority = 0
    username.quiet = True

    def password(self, password):
        """Used to set the connection password, if any."""
        self._password = password
    password.priority = 0
    password.quiet = True

    def address(self, address):
        """Used to set the connection address."""
        self._address = address
    address.priority = 0
    address.quiet = True
    address.required = False
