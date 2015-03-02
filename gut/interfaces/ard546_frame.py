import telnetlib
from frame import Frame

class ARD546_Frame(Frame):
    interfacename = "ard546"    

    @staticmethod        
    def connect(address):
        """ Connection procedure for ard546."""
        try:
            return telnetlib.Telnet(address, 1307, 10)
        except socket.timeout:
            return None

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
        
