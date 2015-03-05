import pexpect
import time
from frame import Frame

class sh_Frame(Frame):
    interfacename = "shell"    
    
    def establishConnection(self):
        """ Connection procedure for remote shell."""
        try:
            con = pexpect.spawn("sh")
        except:
            return None
        con.sendline("PS1=\>; export PS1")
        con.expect("export PS1")
        return con

    def sendframe(self):
        """Transmit a frame object's content to intended recipient."""
        self.connection.sendline(self._send["content"])
        self.connection.expect([">", pexpect.TIMEOUT], timeout=1)        


    def expectmessage(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""
        results = self.connection.expect([pexpect.TIMEOUT] + array, timeout = timer)
        if results == 0:
            return (None, True) # Return no capture, timeout
        else:
            return ((self.connection.before + self.connection.after).decode("utf-8"), False) # Return capture, no timeout
        

    def capturemessage(self):
        """Try to capture text without an "expect" clause."""
        time.sleep(.1)
        try:
            self.connection.expect([">", pexpect.TIMEOUT], timeout=1)
            read_value = self.connection.before
        except:
            read_value = ""
        return read_value.decode("utf-8")
