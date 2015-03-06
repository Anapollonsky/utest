import os
import glob
import sys
import inspect
import importlib
from frame import Frame
import utils as ut

class Conman:
    """Singleton class responsible for tracking program state."""
        
    def __init__(self, trace):
        self.connections = []        
        self.trace_level = trace
        self.update_terminal()
        self.storage = {}
        self.global_permanent = {"capture": None, "connect": None}        
        self.interfaces = []


    def get_interface(self, name):
        """Import specific interface from /interfaces"""

        # Check if it's already stored
        for interface in self.interfaces:
            if interface.interfacename == name:
                return interface
            
        # Try and find it if not
        for file in glob.glob(os.path.join(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + "/interfaces/", "*.py")):
            filename = os.path.splitext(os.path.basename(file))[0]
            module = importlib.import_module('interfaces.' + filename)
            for interfacename, interface in inspect.getmembers(module):
                if inspect.isclass(interface) and hasattr(interface, "interfacename") and interface.interfacename == name:
                    self.interfaces.append(interface)
                    ut.assign_function_attributes(interface, self)
                    self.message(2, "Found interface \"" + name + "\"")
                    return interface

        self.ferror("Unable to find interface \"" + name + "\"")        
        
    ## Connection Management    
    def openconnection(self, frame):
        """Open a connection to target and return, or return existing connection."""
        # Get list of arguments, excluding 'self'.
        argspec = inspect.getargspec(frame.establish_connection)
        args = argspec.args[1:]
        defaults = argspec.defaults or []
        
        # Verify that all expected arguments are present
        covered_indices = [args.index(x) for x in args if hasattr(frame, '_' + x)]
        remaining_args = [x for x in args if args.index(x) not in covered_indices] # leftover arguments to be filled
        remaining_defaults = [x for x in defaults if defaults.index(x) - (len(args) - len(defaults)) not in covered_indices] # leftover defaults
        if len(remaining_args) > len(remaining_defaults):
            self.terror("Not enough arguments for connection, expected " + str(args) + ", available defaults " + str(defaults)) 
            
        # If the connection with identical connection specifications exists, return it.
        for connection in self.connections: 
            connection_exists = True            
            for arg in args + ["interface"]:
                if not ((arg in connection.args) and getattr(frame, '_' + arg) == connection.args[arg]):
                    connection_exists = False
            if connection_exists:
                return connection 
            
        # Populate dictionary to insert as arguments to connection function
        arg_dict = {}        
        for arg in args:
            if hasattr(frame, '_' + arg):                    
                arg_dict[arg] = getattr(frame, '_' + arg)

        conn = frame.establish_connection(**arg_dict)
        if conn == None:
            self.ferror("Unable to establish a connection to interface \"" + frame._interface + "\" with arguments " + str(arg_dict))
        else: 
            self.message(2, "Connected with interface \"" + frame._interface + "\"")
            conn.args = arg_dict
            conn.args["interface"] = frame._interface
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
        print("  > " +  content.strip())
        
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
    
    def update_terminal(self):
        self.terminal = {}
        self.terminal["rows"], self.terminal["cols"] = ut.getTerminalSize()


