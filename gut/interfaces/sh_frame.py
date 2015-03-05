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
        self._connection.sendline(self.args["send"]["content"])
        self._connection.expect([">", pexpect.TIMEOUT], timeout=1)        


    def expectmessage(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""
        results = self._connection.expect([pexpect.TIMEOUT] + array, timeout = timer)
        if results == 0:
            return (None, True) # Return no capture, timeout
        else:
            return ((self._connection.before + self._connection.after).decode("utf-8"), False) # Return capture, no timeout
        

    def capturemessage(self):
        """Try to capture text without an "expect" clause."""
        time.sleep(.1)
        try:
            self._connection.expect([">", pexpect.TIMEOUT], timeout=1)
            read_value = self._connection.before
        except:
            read_value = ""
        return read_value.decode("utf-8")
