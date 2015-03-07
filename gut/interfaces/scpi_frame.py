import time
import telnetlib
import socket
from frame import Frame
from decorators import command

class scpi_Frame(Frame):
    interfacename = "scpi"    

    def establish_connection(self, address, username, password):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 23, 10)
        except socket.timeout:
            return None
        con.expect(['ogin'.encode('ascii')])
        con.write(username.encode('ascii') + b"\n")
        con.expect(['assword'.encode('ascii')])
        con.write(password.encode('ascii') + b"\n")
        time.sleep(.2)
        return con

################################################################################
#################### Command functions

    @command(0, quiet=True)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address
