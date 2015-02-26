import gut_utils as ut
import sys
import pexpect

class Conman:
    """Singleton class responsible for managing pexpect connections and different frame types."""
    connections = []
    
    def __init__(self, trace):
        self.trace_level = trace
        self.updateterminal()

    ## Connection list        
    def ard546connect(address):
        return pexpect.spawn("telnet " + address + " 1307")

    def bciconnect(address):
        con = pexpect.spawn("telnet " + address + " 7006")
        con.expect("ogin")
        con.sendline("lucent")
        con.expect("assword")
        con.sendline("password")
        return con

    def shconnect(address):
        con = pexpect.spawn("telnet " + address)
        con.expect("ogin")
        con.sendline("lucent")
        con.expect("assword")
        con.sendline("password")
        return con

    connfuncdict = {
         "ard546": ard546connect
        ,"sh": shconnect
        ,"bci": bciconnect
    }

    conncommdict = {
         "ard546": "ard546"
        ,"sh": "sh"
        ,"bci": "bci"
    }
    
    ## Connection Management    
    def openconnection(self, interface, address):
        """Open a connection to target and return, or return existing connection."""
        for connection in Conman.connections: # Check if connection exists
            if connection.address == address and connection.interface == interface:
                return connection
        conn = Conman.connfuncdict[interface](address)
        if conn:
            self.message("Connected to " + interface + " at " + address)
        conn.address = address
        conn.interface = interface
        if self.trace_level == 3:
            conn.logfile_read = sys.stdout
        Conman.connections.append(conn)
        return conn

    def sendframe(self, frame):
        """Transmit a frame object's message to intended recipient."""
        if frame.connection not in Conman.connections:
            self.ferror("Frame connection to " + frame.connection.address + " over " + frame.connection.interface + " not found in the connection manager. Exiting.")
        else:
            connection = self.openconnection(frame.connection.interface, frame.connection.address)
            connection.sendline(frame.send["content"])
            return connection

    def closeconnection(self, connection):
        connection.close()
        del connection

    def closeallconnections(self):
        for connection in Conman.connections:
            connection.close()
            del connection

    ## Miscellaneous
    def message(self, message):
        print("" + message.strip())

    def block(self, message):
        print((" " + message.strip() + " ").center(40, "=").center(self.terminal["rows"], " "))

    def hblock(self, message):
        print((" " + message + " ").center(self.terminal["rows"], "="))
        
    def ferror(self, message):
        print((" " + "FATAL ERROR" + " ").center(self.terminal["rows"], "#"))
        print(message.strip())
        sys.exit()

    def terror(self, message):
        print(("  TEST ERROR  ").center(self.terminal["rows"], "#"))
        if isinstance(message, str):
            print(message[0].strip())
        elif isinstance(message, list) and len(message) == 2:
            print(("  Capture  ").center(self.terminal["rows"], "="))            
            print(message[1].strip())        
        sys.exit()
        
    # def notify(self, level, message): 
    #     """Perform formatting of output based on level parameter."""
    #     if level == "bas": # basic message
    #         print("" + message.strip())
    #     elif level == "not": # special notification
    #         print("> " + message.strip())
    #     elif level == "update": # special notification
    #         print(">>> " + message.strip())        
    #     elif level == "tf": # Test Failure
    #         print("###" + message.strip() + "\n Exiting.###")
    #         sys.exit()        
    #     elif level == "fe": # fatal error
    #         print("### " + message.strip() + "\n Exiting. ###")
    #         sys.exit()

    
    def updateterminal(self):
        self.terminal = {}
        self.terminal["rows"], self.terminal["cols"] = ut.getTerminalSize()


