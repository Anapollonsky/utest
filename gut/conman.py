import os
import glob
import sys
import inspect
import importlib
import functools
from colorama import Fore
from interfaces.frame import Frame
import utils as ut

class Conman:
    """ Singleton class responsible for tracking global program state.

    Keeps track of messaging functions, global frame queue, trace level,
    global frame options, global data storage, open connections and interfaces."""
        
    def __init__(self, trace):
        self.connections = []
        self.trace_level = trace
        self.message_functions = self.create_message_functions(trace)
        self.global_permanent = {}
        self.update_terminal()
        self.storage = {}
        self.interfaces = []
        
        
    def get_interface(self, name):
        """ Find an interface by name """

        # Check if it's already stored in conman
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
                    self.message(2, "Found interface \"" + name + "\"")
                    return interface

        self.ferror("Unable to find interface \"" + name + "\"")        
        
    ## Connection Management    
    def openconnection(self, frame):
        """Open a connection

        Format connection arguments to take into account defaults, do error checking.
        Look for existing connection matching parameters, use that if it exists.
        Create a new connection otherwise. """
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

    def create_message_functions(self, level):
        """ Generate the functions that will be used for messaging. """
        def message0(content):
            pass

        def message_color(content, spacing, color):
            content = content.strip()
            if "\n" in content:
                content = "\n" + content
            outstr = spacing + color  + u"\u2771" + " " + Fore.RESET + content.replace("\n", "\n" + spacing)
            return outstr

        # Match color and spacing, where spacing is dependent on trace level.
        message_properties = zip([Fore.GREEN, Fore.YELLOW, Fore.CYAN, Fore.RED], ['  ' * k for k in range(3, -1, -1)])
        # Insert resulting color and spacing into the message_color function for each level
        message_function_list = [functools.partial(message_color, color = color, spacing = spacing) for color, spacing in message_properties]
        # Select correct subset of generated functions, so that the lower-priority functions are omitted depending on the trace level.
        used_messages = message_function_list[(3 - self.trace_level):]
        # Insert empty message function into places where functions were omitted
        message_functions = [message0] *  (4 - len(used_messages)) + used_messages
        return message_functions

    def message(self, level, content):
        """ Select appropriate message function. """
        outstr = self.message_functions[level - 1](content)
        if outstr: print(outstr)
    
    def ferror(self, content):
        """ Fatal error """
        print(Fore.RED + ("  FATAL ERROR  ").center(self.terminal["rows"], "#")+ Fore.RESET)
        print(content.strip())
        sys.exit()

    def terror(self, content):
        """ Test error """
        print(Fore.RED + ("  TEST ERROR  ").center(self.terminal["rows"], "#") + Fore.RESET)
        if isinstance(content, str):
            print(content.strip())
        elif isinstance(content, list) and len(content) == 2:
            print(content[0].strip())
            print(("  Capture  ").center(self.terminal["rows"], "="))            
            print(content[1].strip())        
        sys.exit()

    ## Miscellaneous
    
    def update_terminal(self):
        """ Update stored terminal size values """
        self.terminal = {}
        self.terminal["rows"], self.terminal["cols"] = ut.getTerminalSize()
