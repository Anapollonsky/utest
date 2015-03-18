import pexpect
import time
from interfaces.frame import Interactive_Frame
from decorators import command

class sh_Frame(Interactive_Frame):
    interfacename = "shell"    
    
    def establish_connection(self, shell = "sh"):
        """ Connection procedure for remote shell."""
        try:
            con = pexpect.spawn(shell)
        except:
            return None
        con.sendline("PS1=\>\>; export PS1")
        con.expect("export PS1")
        con.expect(">\>") 
        return con

    def send_frame(self):
        """Transmit a frame object's content to intended recipient."""
        self._connection.sendline(self._send)
        try:
            self._connection.read_nonblocking(size=100, timeout=.01)
        except:
            pass
        # time.sleep(.1)

    def expect_message(self, array, timer):
        """Wait for a message from an array, return either a capture or a timeout."""
        self._prompt_has_been_consumed = True
        results = self._connection.expect([pexpect.TIMEOUT] + array, timeout = timer)
        if results == 0:
            return (None, True) # Return no capture, timeout
        else:
            return ((self._connection.before + self._connection.after).decode("utf-8"), False) # Return capture, no timeout
        
    def capture_message(self):
        """Try to capture text without an "expect" clause."""
        self._connection.expect([">\>", pexpect.TIMEOUT], timeout=1)
        read_value = self._connection.before
        return read_value.decode("utf-8")


################################################################################
#################### Command functions
    @command(0)
    def shell(self, shell = 'sh'):
        """Used to set the shell, if any."""
        self._shell = shell

