import os
import glob
import sys
import inspect
from frame import Frame
import utils as ut

class Conman:
    """Singleton class responsible for tracking program state."""

    def importinterfaces(self):
        """Import valid interfaces from gutdir/interfaces"""
        sys.path.append('interfaces')        
        interfaces = []
        for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/interfaces/", "*.py")):
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
    def openconnection(self, frame):
        """Open a connection to target and return, or return existing connection."""
        # Get list of arguments, excluding 'self'.
        connect_args = inspect.getargspec(frame.establishConnection).args[1:]

        # Verify that all expected arguments are present
        for arg in connect_args + ["interface"]:
            if not hasattr(frame, arg):
                self.ferror("Expected connection argument \"" + arg + "\" not set.")                
                
            
        # If the connection with identical connection specifications exists, return it.
        for connection in self.connections: 
            connection_exists = True            
            for arg in connect_args + ["interface"]:
                if not ((arg in connection.args) and getattr(frame, arg)[arg] == connection.args[arg]):
                    connection_exists = False
            if connection_exists:
                return connection
            
        # Populate dictionary to insert as arguments to connection function
        arg_dict = {}        
        for arg in connect_args:
            if hasattr(frame, arg):                    
                arg_dict[arg] = getattr(frame, arg)[arg]

         # Check if the interface exists, and if it does, use it to connect
        connection_found = False
        for interface in self.interfaces:
            if hasattr(interface, "interfacename") and interface.interfacename == frame.interface["interface"]:
                conn = frame.establishConnection(**arg_dict)
                connection_found = True
                break
        if not connection_found:
            self.ferror("Unable to find interface \"" + frame.interface["interface"] + "\"")
        if conn == None:
            self.ferror("Unable to establish a connection to interface \"" + frame.interface["interface"] + "\" with arguments " + str(arg_dict))
        else: 
            self.message(2, "Connected with interface \"" + frame.interface["interface"] + "\"")
            conn.args = arg_dict
            conn.args["interface"] = frame.interface["interface"]
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
            print(content[0].strip())
            print(("  Capture  ").center(self.terminal["rows"], "="))            
            print(content[1].strip())        
        sys.exit()

    ## Miscellaneous
    
    def updateterminal(self):
        self.terminal = {}
        self.terminal["rows"], self.terminal["cols"] = ut.getTerminalSize()


