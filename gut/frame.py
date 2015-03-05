import time
from copy import deepcopy
import re
import inspect
import utils as ut
import functions.functions as fu
 
class Frame(object):
    """Representation of a sent/received frame."""

    default_func_attrs = {"defaults":{}, "quiet": False, "required": False, "hooks": {}}
    
    def __init__(self, local_settings, conman):
        self.responses = ""
        self.args = {}
        
        def checkFunctionsExist(local_settings, functions, conman):
            """Verify that all the functions specified in local_settings can be found."""
            for func_string in local_settings:
                if func_string not in [func.__name__ for func in functions]:
                    conman.ferror("Unexpected function specified: \"" + func_string + "\"")
                    
            
        def handleAnyEntry(local_settings, func):
            self.args[func.__name__] = local_settings[func.__name__]

        # Construct a list of all available functions that have a priority attribute.
        functions = [method for name, method in Frame.__dict__.items() if (callable(method) and hasattr(method, "priority"))]
        functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority"))]        
        conman.message(3, "Sending " + local_settings["interface"] + " frame")

        checkFunctionsExist(local_settings, functions, conman)

        for func in functions:
            if func.__name__ in local_settings:
                handleAnyEntry(local_settings, func)
        self.conman = conman
        self.conman.updateterminal() # Update the terminal on every frame sent. Not necessary, but performance isn't an issue right now.

        
    def addresponse(self, response):
        self.responses = self.responses + response
        
    def perform_actions(self):
        """Will go through all of the properties of a frame, match them up against available functions, and run them with the proper arguments in the order as determined by the functions' priority"""

        # Look through available functions, check if they're referenced on the frame object, and put those that are on a list.
        functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority") and name in self.args)]

        # Sort by priority in ascending order
        functions.sort(key=lambda x: x.priority)
        for func in functions:
            # Match every value to an argument with the same name as the key of that value.
            if self.args[func.__name__] == None:
                func_args = {}
            else:
                func_args = deepcopy(self.args[func.__name__])

            # print(func_args)
            # print(func.defaults)
            if isinstance(func_args, dict):
                ut.recursive_dict_merge(func_args, func.defaults)

            if (func.quiet == False): 
                self.conman.message(2, "Running " + func.__name__)

            
            argspec = inspect.getargspec(func)

            # Dictionary with argument:value mapping
            if all([x in argspec.args for x in func_args]) and isinstance(func_args, dict):
                for arg in func_args:
                    if arg in func.hooks:
                        for hook in func.hooks[arg]:
                            func_args[arg] = hook(self, func_args[arg])
                func(**func_args)

            # Dictionary being passed directly as argument
            elif isinstance(func_args, dict):
                for arg in func_args:
                    for hook in func.hooks:
                        func_args[arg] = hook(self, func_args[arg])
                func(func_args)

            # List being passed directly as argument
            elif isinstance(func_args, list):
                for arg in func_args:
                    for hook in func.hooks:
                        arg = hook(self, arg)
                func(func_args)

            # Singular value being passed as argument
            else:
                for hook in func.hooks:
                    func_args = hook(self, func_args)                
                func(func_args)

################################################################################
#################### Hooks
    def hook_var_replace(self, string):
        if hasattr(self, "_vars"):
            for variable in self._vars:
                string = re.sub(variable, str(self._vars[variable]), string)
        return string

################################################################################
#################### Callable functions

    def interface(self, interface):
        """Used to set the connection interface. """
        self._interface = interface
        pass
    interface.priority = 0
    interface.quiet = False

    def send(self, content):
        """Send the frame."""
        self._send = content
        self.sendframe()
    send.priority = 4
    send.hooks = [hook_var_replace]

    def capture(self):
        """Capture some data."""
        self.addresponse(self.capturemessage())
    capture.priority = 7
    capture.quiet = False

    def connect(self):
        """Used to initiate the connection."""
        self._connection = self.conman.openconnection(self) 
    connect.priority = 1
    connect.quiet = False

    
    def timeout(self, timeout):
        self._timeout = timeout
        """Used to set the timeout variable, used by expect and expect_regex"""
        pass
    timeout.priority = 0

    def print_time(self, formatting="%H:%M:%S"):
        """High-priority time-print function. Optional argument specifies formatting."""
        self.conman.message(1, strftime(formatting, gmtime()))
    print_time.priority = 0

    def print_response(self):
        """Low-priority function that prints the captured response to the sent message."""
        self.conman.message(1, "\n" + str(self.responses) + "\n")
    print_response.priority = 100    


    def print_send(self):
        """Low-priority function that prints the sent message."""
        self.conman.message(1, "\n" + str(self.send["content"]) + "\n")
    print_send.priority = 100    

    def log(self, filename):
        """Low-priority function to log the sent and received messages to a given file."""
        try:
            infile = open(filename, 'a')
        except IOError:
            self.conman.ferror("Failed to open file " + filename + " for logging.")
        infile.write(self.send["content"] + "\n\n" + self.responses + "\n\n")
        infile.close()
    log.priority = 100
    log.quiet = True

    def reject(self, array):
        """Throw an error if any string in list-argument is present in given frame's responses."""
        if isinstance(array, list):
            if any([re.search(k, self.responses) for k in [re.escape(str(x)) for x in array]]):
                self.conman.terror(["Captured rejected substring in response:" + k.strip(), self.responses])
        else:
            if re.search(re.escape(str(array)), self.responses):
                self.conman.terror(["Captured rejected regex substring in response:" + array.strip(), self.responses])                            
    reject.priority = 8

    def reject_regex(self, array):
        """Throw an error if any regex in list-argument is present in given frame's responses."""
        if isinstance(array, list):
            if any([re.search(str(k), self.responses) for k in array]):
                    self.conman.terror(["Captured rejected regex substring in response:" + k.strip(), self.responses])
        else:
            if re.search(str(array), self.responses):
                self.conman.terror(["Captured rejected regex substring in response:" + array.strip(), self.responses]) 
    reject_regex.priority = 8

    def expect(self, array):
        """Try and capture everything in array before time runs out."""
        print(array)
        diminishing_expect = [re.escape(x) for x in array]
        timer = self._timeout if hasattr(self, "_timeout") else 10
        if hasattr(self, "responses"):
            for k in diminishing_expect[:]:
                if re.search(k, self.responses): 
                    diminishing_expect.remove(k)        
        while diminishing_expect:
            captured_lines_local = [] 
            iter_time = time.time()
            temp_expect = list(diminishing_expect)
            i = self.expectmessage(temp_expect, timer)
            if i[1] == True:
                self.conman.terror(["Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + ".", self.responses])        
            timer -= (time.time() - iter_time) # Subtract time it took to capture
            capture = i[0] # Captured value
            self.addresponse(capture)        
            for k in diminishing_expect[:]:
                if re.search(k, self.responses):
                    captured_lines_local.append(k)
                    diminishing_expect.remove(k)
            for k in captured_lines_local:
                self.conman.message(1, "Captured in response: " + k.strip())
        self._timeout = {"timeout": timer}
    expect.priority = 6

    def expect_regex(self, array):
        """Try and capture everything in array before time runs out."""
        diminishing_expect = array
        timer = self._timeout if hasattr(self, "_timeout") else 10
        if hasattr(self, "responses"):
            for k in diminishing_expect[:]:
                if re.search(k, self.responses):
                    diminishing_expect.remove(k)            
        while diminishing_expect:
            captured_lines_local = [] 
            iter_time = time.time()
            temp_expect = list(diminishing_expect)
            i = self.expectmessage(temp_expect, timer)
            if i[1] == True:
                self.conman.terror(["Timeout while waiting for the following regexes:\n" + str(diminishing_expect) + ".", self.responses])
            timer -= (time.time() - iter_time) # Subtract time it took to capture
            capture = i[0]
            for k in diminishing_expect[:]:
                if re.search(k, capture):
                    captured_lines_local.append(k)
                    diminishing_expect.remove(k)
            for k in captured_lines_local:
                self.conman.message(1, "Captured in response: " + k.strip())
            self.addresponse(capture)
        self._timeout = {"timeout": timer}
    expect_regex.priority = 6


    def store_regex(self, regexes):
        """Capture regexes in responses and store in the storage dictionary. Accepts lists and strings."""
        def store_regex_single(self, regex):
            match = re.search(regex, self.responses)
            if match:
                self.conman.storage[regex] = match.groups()
                self.conman.message(1, "Regex \"" + regex + "\" captured: \"" + str(match.groups()) + "\"")
            else:
                self.conman.terror(["Expected regex \"" + regex + "\" not present in captured self.", self.responses])
        if isinstance(regexes, list):
            for regex in regexes:
                store_regex_single(self, regex)
        elif isinstance(regexes, str):
            store_regex_single(self, regexes)
    store_regex.priority = 10

    def check_regex(self, regexes):
        """Verify that the regexes extracted in the current frame match those stored with store_regex.
        Regexes stored and retrieved based purely on the regex that's used to capture them."""
        def check_regex_single(self, regex):
            match = re.search(regex, self.responses)
            if match:
                if not (self.conman.storage[regex] == match.groups()):
                    self.conman.terror(["Mismatch between captured and stored data for regex \"" + regex + "\".",
                                         "Stored: " + str(self.conman.storage[regex]) +
                                         "\nCaptured: " + str(match.groups())])
                else:
                    self.conman.message(1, "Regex \"" + regex + "\" matches: \"" + str(match.groups()) + "\"")
            else:
                print (self.responses)
                self.conman.terror(["Expected regex " + regex + " not present in captured self.", self.responses]) 
        if isinstance(regexes, list):
            for regex in regexes:
                check_regex_single(self, regex)
        else:
            check_regex_single(self, regexes)
    check_regex.priority = 12

    def vars(self, variables):
        """Replaces all instances of one substring with another."""
        self._vars = variables
    vars.priority = 0
    
