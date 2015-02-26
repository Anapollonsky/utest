import time
import pexpect
import re
import utils as ut
import gut_analyze as an
import inspect
        
class Frame:
    """Representation of a sent/received frame."""
    
    def __init__(self):
        self.responses = []

    def addresponse(self, response):
        self.responses.append(response)
        
    def perform_actions(self):
        """Will go through all of the properties of a frame, match them up against available functions, and
        run them with the proper arguments in the order as determined by the functions' priority"""
        # Look through available functions, check if they're referenced on the frame object, and put those that are on a list.
        functions = [method for name, method in an.__dict__.iteritems() if (callable(method) and hasattr(method, "priority") and hasattr(self, method.__name__))]
        # Sort by priority in ascending order
        functions.sort(key=lambda x: x.priority) 
        
        for func in functions:
            # If the argument is a dictionary of arguments, match every value to a argument with the same name as the key of that value.
            func_args = dict(getattr(self, func.__name__))
            ut.recursive_dict_merge(func_args, func.defaults)
            func_arg_names = inspect.getargspec(func).args
            for k in func_args:
                if k not in func_arg_names:
                    ut.notify("fe", "Unexpected function argument " + k + " for function " + func.__name__ + ".")
            ut.notify("not", "Running function " + func.__name__ + "...")
            func(self, **func_args)


    @staticmethod
    def frameFromLos(conman, los):
        """Generate a frame from a dictionary of local settings."""
        frame = Frame()
        # Construct a list of all available functions that have a priority attribute.
        functions = [method for name, method in an.__dict__.iteritems() if (callable(method) and hasattr(method, "priority"))]
        # Iterate through them, adding them to the frame if an entry exists in the 'local settings' (los) dictionary.
        for func in functions:
            if func.__name__ in los:
                if isinstance(los[func.__name__], dict): # If already in proper dictionary format
                    setattr(frame, func.__name__, los[func.__name__])
                else: # If in compressed format, construct a dictionary. Use name of 2nd function argument as key.
                    setattr(frame, func.__name__, {inspect.getargspec(func)[0][1]: los[func.__name__]})
        frame.conman = conman
        frame.connection = frame.conman.openconnection(los["interface"], los["board"]) 
        frame.conman.updateterminal()
        print frame.conman.terminal.cols
        print frame.conman.terminal.rows
        return frame
