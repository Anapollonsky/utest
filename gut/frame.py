import time
import re
import inspect
import utils as ut
import functions.functions as fu
 
class Frame(object):
    """Representation of a sent/received frame."""

    default_func_attrs = {"defaults":{}, "quiet": False, "required": False}
    
    def __init__(self, local_settings, conman):
        self.responses = ""

        def checkFunctionsExist(local_settings, functions, conman):
            """Verify that all the functions specified in local_settings can be found."""
            for func_string in local_settings:
                if func_string not in [func.__name__ for func in functions]:
                    conman.ferror("Unexpected function specified: \"" + func_string + "\"")
                    
        def handleDictEntry(local_settings, conman, func):
            """If the function entry is a dictionary, verify that every entry matches up against the function argument list."""
            func_args = inspect.getargspec(func).args
            for arg in local_settings[func.__name__]:
                if arg not in func_args:
                    conman.ferror("Unexpected function argument \"" + arg + "\" for function \"" + func.__name__ + "\".")
            # Add to frame object
            setattr(self, func.__name__, local_settings[func.__name__])

        # Construct a list of all available functions that have a priority attribute.
        functions = [method for name, method in Frame.__dict__.items() if (callable(method) and hasattr(method, "priority"))]
        functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority"))]        
        conman.message(3, "Sending " + local_settings["interface"] + " frame")

        checkFunctionsExist(local_settings, functions, conman)

        for func in functions:
            if func.__name__ in local_settings:
                if isinstance(local_settings[func.__name__], dict): # If already in proper dictionary format
                    handleDictEntry(local_settings, conman, func)
                elif local_settings[func.__name__] == None:
                    setattr(self, "_" + func.__name__, None)        
                else: 
                    # If in compressed format, construct a dictionary. Use name of 2nd function argument as key. Add to frame object.
                    setattr(self, "_" + func.__name__, {inspect.getargspec(func)[0][1]: local_settings[func.__name__]})
        self.conman = conman
        self.conman.updateterminal() # Update the terminal on every frame sent. Not necessary, but performance isn't an issue right now.

        
    def addresponse(self, response):
        self.responses = self.responses + response
        
    def perform_actions(self):
        """Will go through all of the properties of a frame, match them up against available functions, and run them with the proper arguments in the order as determined by the functions' priority"""
        # Look through available functions, check if they're referenced on the frame object, and put those that are on a list.
        functions = [getattr(self, name) for name in dir(self) if (callable(getattr(self, name)) and hasattr(getattr(self, name), "priority") and hasattr(self, "_" + name))]
        print(functions)
        # print (dir(self))
        # Sort by priority in ascending order
        functions.sort(key=lambda x: x.priority)
        for func in functions:
            # The argument is a dictionary of arguments, match every value to an argument with the same name as the key of that value.
            if getattr(self, "_" + func.__name__) != None:
                func_args = dict(getattr(self, "_" + func.__name__))
            else:
                func_args = {}
            ut.recursive_dict_merge(func_args, func.defaults)
            # func_arg_names = inspect.getargspec(func).args
            
            if (func.quiet == False): 
                self.conman.message(2, "Running " + func.__name__)
            func(**func_args)
            

    def interface(self, interface):
        """Used to set the connection interface. """
        pass
    interface.priority = 0
    interface.quiet = True
    interface.required = True

    def send(self, content):
        """Send the frame."""
        self.sendframe()
    send.priority = 4
    send.required = True

    def capture(self):
        """Capture some data."""
        self.addresponse(self.capturemessage())
    capture.priority = 7
    capture.required = True
    capture.quiet = False

    def connect(self):
        """Used to initiate the connection."""
        self.connection = self.conman.openconnection(self) 
    connect.priority = 1
    connect.required = True
    connect.quiet = True

    
    def timeout(self, timeout):
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
        diminishing_expect = [re.escape(x) for x in array]
        timer = self._timeout["timeout"] if hasattr(self, "_timeout") else 10
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
        timer = self._timeout["timeout"] if hasattr(self, "_timeout") else 10
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
