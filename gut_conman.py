import gut_utils as ut
import sys
import telnetlib
import socket

class Conman:
    """Singleton class responsible for tracking program state."""

    def __init__(self, trace):
        self.connections = []        
        self.trace_level = trace
        self.updateterminal()
        self.storage = {}
        
    ## Connection list        
    def ard546connect(address):
        """ Connection procedure for ard546."""
        try:
            return telnetlib.Telnet(address, 1307, 10)
        except socket.timeout:
            return None
        
    def bciconnect(address):
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

    def shconnect(address):
        """ Connection procedure for remote shell."""
        try:
            con = telnetlib.Telnet(address, 23, 10)
        except socket.timeout:
            return None        
        con.expect(["ogin"])
        con.write("lucent\n")
        con.expect(["assword"])
        con.write("password\n")
        return con

    connfuncdict = {
         "ard546": ard546connect
        ,"sh": shconnect
        ,"bci": bciconnect
    }

    ## Connection Management    
    def openconnection(self, interface, address):
        """Open a connection to target and return, or return existing connection."""
        for connection in self.connections: # Check if connection exists
            if connection.address == address and connection.interface == interface:
                return connection
        conn = Conman.connfuncdict[interface](address)
        if conn == None:
            self.ferror("Unable to establish a connection to " + address + " via " + interface + ".")
        if conn:
            self.message(2, "Connected to " + interface + " at " + address)
        conn.address = address
        conn.interface = interface
        self.connections.append(conn)
        return conn

    def sendframe(self, frame):
        """Transmit a frame object's content to intended recipient."""
        connection = self.openconnection(frame.connection.interface, frame.connection.address)
        connection.write(frame.send["content"] + "\n")
        return connection

    def closeconnection(self, connection):
        """ Close a connection """
        connection.close()
        del connection

    def closeallconnections(self):
        """ Close all the connections."""
        for connection in self.connections:
            connection.close()
            del connection

    # Messaging
    def message0(self, content):
        pass

    def message1(self, content):
        print("  > " + content.strip())
        
    def message2(self, content):
        print(content.strip())

    def message3(self, content):
        print((" " + content.strip() + " ").center(40, "=").center(self.terminal["rows"], " "))

    def message4(self, content):
        print((" " + content + " ").center(self.terminal["rows"], "="))

    message_functions = [message0, message0, message0, message1, message2, message3, message4]
    
    def message(self, level, content):
        self.message_functions[self.trace_level + level - 1](self, content)
        
    
    def ferror(self, content):
        print((" " + "FATAL ERROR" + " ").center(self.terminal["rows"], "#"))
        print(content.strip())
        sys.exit()

    def terror(self, content):
        print(("  TEST ERROR  ").center(self.terminal["rows"], "#"))
        if isinstance(content, str):
            print(content.strip())
        elif isinstance(content, list) and len(content) == 2:
            print(("  Capture  ").center(self.terminal["rows"], "="))            
            print(content[1].strip())        
        sys.exit()

    ## Miscellaneous
    
    def updateterminal(self):
        self.terminal = {}
        self.terminal["rows"], self.terminal["cols"] = ut.getTerminalSize()


