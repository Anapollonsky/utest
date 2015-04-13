from time import sleep
import telnetlib
import socket
from Interface import Interactive_Interface

class SCPI(Interactive_Interface):

    def connect(self, address):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 5023, 10)
        except socket.timeout:
            return None
        sleep(.8)
        con.read_very_eager()
        self._address = address
        self._connection = con

    def expect(self, array, timer = 10):
        """Wait for a message from an array, return either a capture and everything
        preceding it or None in the event of a timeout."""
        array = [array] if isinstance(array, str) else array
        results = self._connection.expect([x.encode('ascii') for x in array], timer)
        if results[0] == -1:
            return None
        else:
            return results[2].decode('ascii')

    def sendline(self, text):
        """Transmit a frame object's content to intended recipient."""
        self._connection.write(text.encode('ascii') + b"\n")
        sleep(.2)

    def capture(self):
        """Try to capture text without an "expect" clause."""
        sleep(.3)
        return self._connection.read_very_eager().decode('ascii')        

    def close(self):
        self._connection.close()

