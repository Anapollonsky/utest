import telnetlib
from frame import Frame

class BCI_Frame(Frame):
    interfacename = "bci"
    
    @staticmethod            
    def connect(address):
        """ Connection procedure for bci."""
        try:
            con = telnetlib.Telnet(address, 7006, 10)
        except socket.timeout:
            return None
        con.expect(["ogin"])
        con.write("lucent\n")
        con.expect(["assword"])
        con.write("password\n")
        return con

    def sendframe(self):
        """Transmit a frame object's content to intended recipient."""
        connection = self.conman.openconnection(self.interface["interface"], self.address["address"])
        connection.write(self.send["content"] + "\n")
        return connection

    def expectmessage(self, array, timer):
        results = self.connection.expect(array, timer)
        if results[0] == -1:
            return (None, True) # Return no capture, timeout
        else:
            return (results[2], False) # Return capture, no timeout
