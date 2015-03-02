import telnetlib
import time
from frame import Frame

class BCI_Frame(Frame):
    interfacename = "bci"
    
    @staticmethod            
    def connect(address, username="lucent", password="password"):
        """ Connection procedure for bci."""
        try:
            con = telnetlib.Telnet(address, 7006, 10)
        except socket.timeout:
            return None
        con.expect(["ogin"])
        con.write(username + "\n")
        con.expect(["assword"])
        con.write(password + "password\n")
        return con

    def sendframe(self):
        """Transmit a frame object's content to intended recipient."""
        connection = self.conman.openconnection(self.interface["interface"], self.address["address"])
        connection.write(self.send["content"] + "\n")
        return connection

    def expectmessage(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""
        results = self.connection.expect(array, timer)
        if results[0] == -1:
            return (None, True) # Return no capture, timeout
        else:
            return (results[2], False) # Return capture, no timeout

    def capturemessage(self):
        """Try to capture text without an "expect" clause."""
        time.sleep(.1)
        return self.connection.read_very_eager()
        
