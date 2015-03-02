import os
import glob
import sys
import socket
import inspect
from frame import Frame
import utils as ut

class Conman:
    """Singleton class responsible for tracking program state."""

    def importinterfaces(self):
        """Import valid interfaces from gutdir/interfaces"""
        sys.path.append('interfaces')        
        interfaces = []
        for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)) + "/interfaces/", "*.py")):
            filename = os.path.splitext(os.path.basename(file))[0]
            module = __import__(filename)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, "interfacename"):
                    interfaces.append(obj)
        interfaces = list(set(interfaces))
        return interfaces
                
    def __init__(self, trace):
        self.connections = []        
        self.trace_level = trace
        self.updateterminal()
        self.storage = {}
        self.global_permanent = {"capture": None, "connect": None}        
        self.interfaces = self.importinterfaces()
        
        
    ## Connection Management    
    def openconnection(self, reqinterface, reqaddress, *extrargs):
        """Open a connection to target and return, or return existing connection."""
        for connection in self.connections: # Check if connection exists
            if connection.address == reqaddress and connection.interface == reqinterface:
                return connection
        for interface in self.interfaces: # Check if the interface exists, and if it does, use it to connect
            if hasattr(interface, "interfacename") and interface.interfacename == reqinterface:
                conn = interface.connect(reqaddress, *extrargs)
        if conn == None:
            self.ferror("Unable to establish a connection to " + reqaddress + " via " + reqinterface + ".")
        if conn:
            self.message(2, "Connected to " + reqinterface + " at " + reqaddress)
        conn.address = reqaddress
        conn.interface = reqinterface
        self.connections.append(conn)
        return conn

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
        instr = (" " + content.strip() + " ")
        print(instr.center(max(len(instr) + 4, 46), "_").center(self.terminal["rows"], " "))


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


