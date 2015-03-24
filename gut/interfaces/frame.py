from copy import deepcopy
import time
import types
import re
import inspect
import operator
import utils as ut
from decorators import command, hook

class Frame(object):
    """Representation of a sent/received frame.

    Contains hooks, command functions, and 'paperwork'."""

    default_func_attrs = {"hooks": {}}
    global_permanent = {}
    default_function = None

    def __init__(self, local_settings, conman):
        """ Initialize a frame

        Verify that all called command functions are present.
        Parse arguments to each command function properly."""
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
        """ Execute all command functions of a frame.

        Goes through frame properties, add them to function queue if arguments for them exist.
        Sort the function queue, so that functions are executed according to priority.
        Run hook functions on relevant arguments, with slightly different behaviors depending
        on whether the hooks variable is a list or a dictionary.
        Execute each resulting function and argument set."""

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
        """ Create a copy of an existing command function """
        newfunction = types.FunctionType(function.__code__, function.__globals__, name or (function.__name__ + "(" + top_function.__name__ + ")"), function.__defaults__, function.__closure__)
        newfunction.priority = priority
        newfunction.hooks = function.hooks
        newfunction.derived = True
        newfunction.quiet = function.quiet
        # print("Derived: " + str(getattr(getattr(self, inspect.stack()[1][3]), "derived")))
        setattr(self, newfunction.__name__, newfunction)
        return newfunction

    def insertFunction(self, function, args = {}):
        """ Insert a function in the appropriate place in the command queue """
        self.functions.append(getattr(self, function.__name__))
        self.functions.sort(key=lambda x: x.priority)
        self.args[function.__name__] = args

    @staticmethod
    def compute(input1, input2, operation):
        ops = {"+": operator.add,
               "-": operator.sub,
               "*": operator.mul,
               "/": operator.truediv}
        if isinstance(input1, dict):
            input1 = compute(**input1)
        if isinstance(input2, dict):
            input2 = compute(**input2)
        return ops[operation](float(input1), float(input2))
        
################################################################################
#################### Hooks
    @hook()
    def hook_var_replace(self, sequence):
        """ Hook that replaces appropriate arguments with their variable replacements. """
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
        """ Hook that prints out all arguments """
        if hasattr(self, "_show_args"):
            self.conman.message(1, "Argument: \"" + str(string) + "\"")
        return string


################################################################################
#################### Command Functions

    @command(0, [hook_show_args], quiet = True)
    def interface(self, interface):
        """ Set the connection interface """
        self._interface = interface

    @command(0, quiet = True)
    def show_args(self):
        """ Activate the 'hook_show_args' hook """
        self._show_args = True

    @command(1, quiet=True)
    def connect(self):
        """ Initiate the connection """
        self._connection = self.conman.openconnection(self)

    @command(0, [hook_show_args])
    def print_time(self, formatting="%H:%M:%S"):
        """ High-priority time-print function. Optional argument specifies formatting """
        self.conman.message(1, time.strftime(formatting, time.gmtime()))

    @command(100, [hook_show_args])
    def log(self, filename):
        """ Low-priority function to log the sent and received messages to a given file """
        try:
            infile = open(filename, 'a')
        except IOError:
            self.conman.ferror("Failed to open file " + filename + " for logging.")
        infile.write(self._send + "\n\n" + self._response + "\n\n")
        infile.close()

    @command(0, [hook_show_args], quiet = True)
    def vars(self, dict):
        """ Replaces all instances of one substring with another. Reliant on a hook """
        self._vars = dict

    @command(-1, [hook_show_args])
    def wait_before(self, wait_time):
        """ Wait before doing anything else """
        time.sleep(wait_time)

    @command(101, [hook_show_args])
    def wait_after(self, wait_time):
        """ Wait after doing everything else """
        time.sleep(wait_time)

class Interactive_Frame(Frame):
    """ Extension of Frame class that implements functions useful for generic
    conversations with the target """

    # Implicitly run these command functions
    global_permanent = {"capture": None, "connect": None}
    default_function = "send"
################################################################################
#################### Hooks


################################################################################
#################### Command Functions

    @command(4, [Frame.hook_var_replace, Frame.hook_show_args])
    def send(self, content):
        """ Send the frame. """
        self._send = content
        self.send_frame()

    @command(7, [Frame.hook_show_args], quiet=True)
    def capture(self):
        """ Capture some data. """
        self._response += self.capture_message()

    @command(100)
    def print_response(self):
        """ Print the captured response. """
        self.conman.message(1, self._response)

    @command(5)
    def print_send(self):
        """ Print what is being sent with 'send'. """
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
    def expect(self, array, regex = False, timeout = 10):
        """Expect to capture strings

        Tries to capture all members in an array of strings or regexes before time runs out"""
        if not isinstance(array, list): array = [array]
        diminishing_expect = [re.escape(x) for x in array] if regex == False else array
        timer = int(timeout)
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
    def store_regex(self, regexes, store_as = None):
        """Capture regexes in responses and store in the storage dictionary.

        The regexes argument is either a string representing a regex or a list of such strings.
        The optional store_as argument takes either string or a list of strings, same type as
        the regexes variable, that is used to specify the index under which the capture will be
        stored.
        """

        # Store as the regex index, if not separately set
        if store_as == None and isinstance(regexes, list):
            store_as = list(regexes)
        elif store_as == None:
            store_as = str(regexes)

        # Ensure that type is now the same
        if not ((isinstance(regexes, list) and isinstance(store_as, list)) or (isinstance(regexes, str) and isinstance(store_as, str))):
            self.conman.ferror("Unexpected regexes and store_as: " + str(regexes) + " | " + str(store_as))

        # Function to deal with singular value
        def store_regex_single(self, regex, store):
            match = re.search(regex, self._response)
            if match:
                self.conman.storage[store] = match.groups()
                self.conman.message(1, "Regex \"" + regex + "\" captured: \"" + str(match.groups()) + "\", stored as \"" + str(store) + "\"")
            else:
                self.conman.terror(["Expected regex \"" + regex + "\" not present in captured string.", self._response])

        # Either loop through all values or deal with single value
        if isinstance(regexes, list):
            for regex, store in zip(regexes, store_as):
                store_regex_single(self, regex, store)
        elif isinstance(regexes, str):
            store_regex_single(self, regexes, store_as)

    @command(12, [Frame.hook_var_replace, Frame.hook_show_args])
    def check_regex(self, regexes, check_as = None):
        """Capture regexes in responses and ensure captures match those in the storage dictionary.

        The regexes argument is either a string representing a regex or a list of such strings.
        The optional check_as argument takes either string or a list of strings, same type as
        the regexes variable, that is used to specify the index under which the capture will be
        checked. """

        # Store as the regex index, if not separately set
        if check_as == None and isinstance(regexes, list):
            check_as = list(regexes)
        elif check_as == None:
            check_as = str(regexes)

        # Ensure that type is now the same
        if not ((isinstance(regexes, list) and isinstance(check_as, list)) or (isinstance(regexes, str) and isinstance(check_as, str))):
            self.conman.ferror("Unexpected regexes and check_as: " + str(regexes) + " | " + str(check_as))

        def check_regex_single(self, regex, check):
            match = re.search(regex, self._response)
            if match:
                if not (self.conman.storage[check] == match.groups()):
                    self.conman.terror(["Mismatch between captured and stored data for index \"" + check + "\".",
                                         "Stored: " + str(self.conman.storage[check]) +
                                         "\nCaptured: " + str(match.groups())])
                else:
                    self.conman.message(1, "Regex \"" + regex + "\" stored as \"" + check + "\" matches: \"" + str(match.groups()) + "\"")
            else:
                self.conman.terror(["Expected regex " + regex + " not present in captured string.", self._response])
        if isinstance(regexes, list):
            for regex, check in zip(regexes, check_as):
                check_regex_single(self, regex, check)
        else:
            check_regex_single(self, regexes, check_as)


    @command(13, [Frame.hook_var_replace, Frame.hook_show_args])
    def check_number(self, input1, input2, operation):
        ops = {"=": operator.eq,
               "!=": operator.ne,
               "<": operator.lt,
               ">": operator.gt,
               ">=": operator.ge,
               "<=": operator.le}
        if isinstance(input1, dict):
            input1 = [Frame.compute(**input1)]
        else:
            try:
                input1 = [float(input1)]
            except ValueError:
                input1 = [float(x) for x in self.conman.storage[input1]]
        if isinstance(input2, dict):
            input2 = [Frame.compute(**input2)]
        else:
            try:
                input2 = [float(input2)]
            except ValueError:
                input2 = [float(x) for x in self.conman.storage[input2]]
        if operation not in ops:
            self.conman.ferror("Invalid operator for check_number: \"" + operation + "\"")
        for x in input1:
            for y in input2:
                if not ops[operation](x, y):
                    self.conman.terror("check_number test failed: " + str(input1) + str(operation) + str(input2) + " is false.") 

    
    @command(5, [Frame.hook_show_args])
    def wait_after_send(self, wait_time):
        time.sleep(wait_time)
