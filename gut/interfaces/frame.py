from copy import deepcopy
import time
import types
import re
import inspect
import utils as ut
from decorators import command, hook

class Frame(object):
    """Representation of a sent/received frame."""

    default_func_attrs = {"hooks": {}}
    global_permanent = {}
    
    def __init__(self, local_settings, conman):
        """ Initialize a frame, handling different input argument types and whatnot."""
        self._response = ""
        self.args = {}
        ut.recursive_dict_merge(local_settings, self.__class__.global_permanent)
        
        def check_functions_exist(local_settings, functions, conman):
            """Verify that all the functions specified in local_settings can be found."""
            for func_string in local_settings:
                if func_string not in [func.__name__ for func in functions]:
                    conman.ferror("Unexpected function specified: \"" + func_string + "\"")
                    
        def handle_parametric_entry(local_settings, func, conman, argspec):
            """Handle parametric argument set."""
            args = argspec.args[1:]
            defaults = argspec.defaults or []
            covered_indices = [args.index(x) for x in local_settings[func.__name__]] # arg indices that are covered in passed arguments
            remaining_args = [x for x in args if args.index(x) not in covered_indices] # leftover arguments to be filled 
            remaining_defaults = [x for x in defaults if defaults.index(x) - (len(args) - len(defaults)) not in covered_indices] # leftover defaults
            if len(remaining_args) > len(remaining_defaults):
                conman.terror("Not enough arguments for function \"" + func.__name__ + "\": Expected " + str(args) + "\"")            
            else: 
                self.args[func.__name__] = local_settings[func.__name__]

        def handle_empty_entry(local_settings, func, conman, argspec):
            """Handle empty argument set."""
            args = argspec.args[1:]
            defaults = argspec.defaults or [] 
            if len(args) > len(defaults):
                conman.terror("Not enough arguments for function \"" + func.__name__ + "\": Expected " + str(args) + "\"")
            else:
                self.args[func.__name__] = {}
                
        def handle_single_entry(local_settings, func, conman, argspec):
            """Handle nonlabeled single argument set."""
            args = argspec.args[1:]
            defaults = argspec.defaults or []
            if len(args) > len(defaults) + 1:
                conman.terror("Not enough arguments for function \"" + func.__name__ + "\": Expected " + str(args) + "\"")
            else:
                self.args[func.__name__] = {args[0]: local_settings[func.__name__]}

        # Construct a list of all available functions that have a priority attribute.
        functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority"))]        
        conman.message(3, "Sending " + local_settings["interface"] + " frame")

        check_functions_exist(local_settings, functions, conman)

        for func in functions:
            if func.__name__ in local_settings:
                argspec = inspect.getargspec(func)                 
                # If the passed argument is a dictionary that looks like it's assignment a data structure to each function argument
                if isinstance(local_settings[func.__name__], dict) and all([x in inspect.getargspec(func).args for x in local_settings[func.__name__]]):
                    handle_parametric_entry(local_settings, func, conman, argspec)
                # If the passed argument is empty
                elif local_settings[func.__name__] == None:
                    handle_empty_entry(local_settings, func, conman, argspec) 
                # If the passed argument is something else
                else:
                    handle_single_entry(local_settings, func, conman, argspec) 
        self.conman = conman
        self.conman.update_terminal() # Update the terminal on every frame sent. Not necessary, but performance isn't an issue right now.
                
    def perform_actions(self):
        """Will go through all of the properties of a frame, match them up against available functions, and run them with the proper arguments in the order as determined by the functions' priority"""

        # Look through available functions, check if they're referenced on the frame object, and put those that are on a list.
        self.functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority") and name in self.args)]

        # Sort by priority in ascending order
        self.functions.sort(key=lambda x: x.priority)
        while self.functions:
            func = self.functions.pop(0)
            # Match every value to an argument with the same name as the key of that value.
            if self.args[func.__name__] == None:
                func_args = {}
            else:
                func_args = deepcopy(self.args[func.__name__])

            if func.quiet == False:
                self.conman.message(2, "Running " + func.__name__)
            
            for arg in func_args:
                if isinstance(func.hooks, dict) and (arg in func.hooks):
                    for hook in func.hooks[arg]:
                        func_args[arg] = hook(self, func_args[arg])
                elif isinstance(func.hooks, list):
                    for hook in func.hooks:
                        func_args[arg] = hook(self, func_args[arg])

            ## Run function, with self as first argument for derived functions.
            if func.derived == False:
                func(**func_args)
            else:
                func(self, **func_args)                

    def deriveFunctionWithPriority(self, top_function, function, priority, name=None):
        """Create a copy of an existing command function with a specified priority and optionally name"""
        newfunction = types.FunctionType(function.__code__, function.__globals__, name or (function.__name__ + "(" + top_function.__name__ + ")"), function.__defaults__, function.__closure__)
        newfunction.priority = priority
        newfunction.hooks = function.hooks
        newfunction.derived = True
        newfunction.quiet = function.quiet
        # print("Derived: " + str(getattr(getattr(self, inspect.stack()[1][3]), "derived")))
        setattr(self, newfunction.__name__, newfunction)
        return newfunction
                
    def insertFunction(self, function, args = {}):
        """Create a copy of a function with priority and insert it in the appropriate place in the command queue."""
        self.functions.append(getattr(self, function.__name__))
        self.functions.sort(key=lambda x: x.priority)
        self.args[function.__name__] = args
        
################################################################################
#################### Hooks
    @hook()
    def hook_var_replace(self, sequence):
        if hasattr(self, "_vars"):
            if isinstance(sequence, list): # if input is list, replace in every member
                for member in sequence:
                    for variable in self._vars:
                        member = re.sub(variable, str(self._vars[variable]), member)
            elif isinstance(sequence, dict): # if input is dictionary, replace in every value
                for member in sequence:
                    for variable in self._vars:
                        sequence[member] = re.sub(variable, str(self._vars[variable]), sequence[member])
            else:
                for variable in self._vars: # if input is anything else, replace as string
                    sequence = re.sub(variable, str(self._vars[variable]), str(sequence))
        return sequence

    @hook()
    def hook_show_args(self, string):
        if hasattr(self, "_show_args"):
            self.conman.message(1, "Argument: \"" + str(string) + "\"")
        return string
        

################################################################################
#################### Command Functions

    @command(0, [hook_show_args], quiet = True)
    def interface(self, interface):
        """Used to set the connection interface. """
        self._interface = interface

    @command(0, quiet = True)
    def show_args(self):
        self._show_args = True

    @command(1, quiet=True)
    def connect(self):
        """Used to initiate the connection."""
        self._connection = self.conman.openconnection(self) 
        
    @command(0, [hook_show_args])
    def timeout(self, timeout):
        """Used to set the timeout variable, used by expect and expect_regex"""        
        self._timeout = timeout

    @command(0, [hook_show_args])
    def print_time(self, formatting="%H:%M:%S"):
        """High-priority time-print function. Optional argument specifies formatting."""
        self.conman.message(1, time.strftime(formatting, time.gmtime()))

    @command(100, [hook_show_args])
    def log(self, filename):
        """Low-priority function to log the sent and received messages to a given file."""
        try:
            infile = open(filename, 'a')
        except IOError:
            self.conman.ferror("Failed to open file " + filename + " for logging.")
        infile.write(self._send + "\n\n" + self._response + "\n\n")
        infile.close()

    @command(0, [hook_show_args])
    def vars(self, dict):
        """Replaces all instances of one substring with another. Reliant on a hook"""
        self._vars = dict

    @command(-1, [hook_show_args])
    def wait_before(self, wait_time):
        time.sleep(wait_time)

    @command(100, [hook_show_args])
    def wait_after(self, wait_time):
        time.sleep(wait_time) 
        
class Interactive_Frame(Frame):

    global_permanent = {"capture": None, "connect": None}    
################################################################################
#################### Hooks

    
################################################################################
#################### Command Functions
    
    @command(4, [Frame.hook_var_replace, Frame.hook_show_args])
    def send(self, content):
        """Send the frame."""
        self._send = content
        self.send_frame()

    @command(7, [Frame.hook_show_args], quiet=True)
    def capture(self):
        """Capture some data."""
        self._response += self.capture_message()

    @command(100)
    def print_response(self):
        self.conman.message(1, self._response)

    @command(5)
    def print_send(self):
        self.conman.message(1, self._send)
        
    @command(8, [Frame.hook_show_args])
    def reject(self, array, regex = False):
        """Throw an error if any string in list-argument is present in given frame's responses."""
        if isinstance(array, list):
            if regex == True and any([re.search(k, self._response) for k in [str(x) for x in array]]):
                self.conman.terror(["Captured rejected regex in response:" + k.strip(), self._response])
            elif regex == False and any([x in self._response for x in array]):
                self.conman.terror(["Captured rejected substring in response:" + k.strip(), self._response])                
        else:
            if regex == True and re.search(str(array), self._response):
                self.conman.terror(["Captured rejected regex in response:" + array.strip(), self._response])
            elif regex == False and str(array) in self._response:
                self.conman.terror(["Captured rejected substring in response:" + array.strip(), self._response])                

    @command(6, [Frame.hook_var_replace, Frame.hook_show_args])
    def expect(self, array, regex = False):
        """Try and capture everything in array before time runs out."""
        diminishing_expect = [re.escape(x) for x in array] if regex == False else array
        timer = self._timeout if hasattr(self, "_timeout") else 10
        if hasattr(self, "_response"):
            for k in diminishing_expect[:]:
                if re.search(k, self._response): 
                    diminishing_expect.remove(k)        
        while diminishing_expect:
            captured_lines_local = [] 
            iter_time = time.time()
            temp_expect = list(diminishing_expect)
            i = self.expect_message(temp_expect, timer)
            if i[1] == True:
                self.conman.terror(["Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + ".", self._response])        
            timer -= (time.time() - iter_time) # Subtract time it took to capture
            self._response += i[0] # Captured Value
            for k in diminishing_expect[:]:
                if re.search(k, self._response):
                    captured_lines_local.append(k)
                    diminishing_expect.remove(k)
            for k in captured_lines_local:
                self.conman.message(1, "Captured in response: " + k.strip())
        self._timeout = {"timeout": timer}

    @command(10, [Frame.hook_var_replace, Frame.hook_show_args])
    def store_regex(self, regexes):
        """Capture regexes in responses and store in the storage dictionary. Accepts lists and strings."""
        def store_regex_single(self, regex):
            match = re.search(regex, self._response)
            if match:
                self.conman.storage[regex] = match.groups()
                self.conman.message(1, "Regex \"" + regex + "\" captured: \"" + str(match.groups()) + "\"")
            else:
                self.conman.terror(["Expected regex \"" + regex + "\" not present in captured self.", self._response])
        if isinstance(regexes, list):
            for regex in regexes:
                store_regex_single(self, regex)
        elif isinstance(regexes, str):
            store_regex_single(self, regexes)

    @command(12, [Frame.hook_var_replace, Frame.hook_show_args])
    def check_regex(self, regexes):
        """Verify that the regexes extracted in the current frame match those stored with store_regex.
        Regexes stored and retrieved based purely on the regex that's used to capture them."""
        def check_regex_single(self, regex):
            match = re.search(regex, self._response)
            if match:
                if not (self.conman.storage[regex] == match.groups()):
                    self.conman.terror(["Mismatch between captured and stored data for regex \"" + regex + "\".",
                                         "Stored: " + str(self.conman.storage[regex]) +
                                         "\nCaptured: " + str(match.groups())])
                else:
                    self.conman.message(1, "Regex \"" + regex + "\" matches: \"" + str(match.groups()) + "\"")
            else:
                self.conman.terror(["Expected regex " + regex + " not present in captured self.", self._response]) 
        if isinstance(regexes, list):
            for regex in regexes:
                check_regex_single(self, regex)
        else:
            check_regex_single(self, regexes)

    @command(5, [Frame.hook_show_args])
    def wait_after_send(self, wait_time):
        time.sleep(wait_time)
