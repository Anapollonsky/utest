import pexpect
import time
from Interface import Interactive_Interface 

class Shell(Interactive_Interface):
    
    def connect(self, shell = "sh"):
        """ Connection procedure for remote shell."""
        try:
            con = pexpect.spawn(shell)
        except:
            return None
        con.sendline("PS1=\>\>; export PS1")
        con.expect("export PS1")
        con.expect(">\>") 
        self._connection = con
        self._shell = shell

    __init__ = connect
        
    def sendline(self, text):
        """Transmit a frame object's content to intended recipient."""
        self._connection.sendline(text)
        try:
            self._connection.read_nonblocking(size=1000, timeout=.01)
        except:
            pass
        time.sleep(.1)

    def expect(self, array, timer = 10):
        """Wait for a message from an array, return either a capture or a timeout."""
        array = [array] if isinstance(array, str) else array
        results = self._connection.expect([pexpect.TIMEOUT] + array, timeout = timer)
        if results == 0:
            return None
        else:
            return (self._connection.before + self._connection.after).decode("utf-8")        

    def capture(self):
        """Try to capture text without an "expect" clause."""
        self._connection.expect([">\>", pexpect.TIMEOUT], timeout=1)
        return self._connection.before.decode("utf-8")

    def close(self):
        self._connection.close()
