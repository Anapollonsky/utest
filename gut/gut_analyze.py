import time
import re
import telnetlib
import gut_utils as ut

# Describe the default attributes of functions. These are used for all functions if not otherwise
# explicitly set. Priority is excluded because a function without a defined priority cannot be run.
default_func_attrs = {"defaults":{}, "quiet": False}

################################################################################
## Function definitions go below this line. Keep it neat.
def timeout(frame, timeout):
    """Used to set the timeout variable, used by expect and expect_regex"""
    pass
timeout.priority = 0

def address(frame, address):
    """Used to set the connection address."""
    pass
address.priority = 0
address.quiet = True

def interface(frame, interface):
    """Used to set the connection interface. """
    pass
interface.priority = 0
interface.quiet = True

def send(frame, content):
    frame.conman.sendframe(frame)
send.priority = 4

def reject(frame, array):
    """Throw an error if any string in list-argument is present in given frame's responses."""
    for capture in frame.responses:
        if any([re.search(k, capture) for k in [re.escape(x) for x in array]]):
            frame.conman.terror(["Captured rejected substring in response:" + k.strip(), "".join(frame.responses)])
reject.priority = 8

def reject_regex(frame, array):
    """Throw an error if any regex in list-argument is present in given frame's responses."""
    for capture in frame.responses:
        if any([re.search(k, capture) for k in array]):
            frame.conman.terror(["Captured rejected regex substring in response:" + k.strip(), "".join(frame.responses)])
reject_regex.priority = 8

def expect(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = [re.escape(x) for x in array]
    timer = frame.timeout["timeout"] if hasattr(frame, "timeout") else 10 
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        i = frame.connection.expect(temp_expect, timer)
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = i[2]
        if i[0] == -1:
            frame.conman.terror("Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + ".")
        for k in diminishing_expect[:]:
            if re.search(k, capture):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            frame.conman.message(1, "Captured in response: " + k.strip())
        frame.addresponse(capture)
expect.priority = 6

def expect_regex(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = array
    timer = frame.timeout["timeout"] if hasattr(frame, "timeout") else 10     
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        i = frame.connection.expect(temp_expect, timer)
        if i[0] == -1:
            frame.conman.terror( "Timeout while waiting for the following regexes:\n" + str(diminishing_expect) + ".")
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = i[2]
        for k in diminishing_expect[:]:
            if re.search(k, capture):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            frame.conman.message(1, "Captured in response: " + k.strip())
        frame.addresponse(capture)
expect_regex.priority = 6

def wait_after(frame, wait_time):
    """Low-priority wait function"""
    time.sleep(wait_time)
wait_after.priority = 100
wait_after.defaults = {"wait_time":.2}

def wait_before(frame, wait_time):
    """High-priority wait function"""
    time.sleep(wait_time)
wait_before.priority = 0
wait_before.defaults = {"wait_time":.2}    

def variable_replace(frame, var_in_dict):
    """Replaces all instances of one word with another in all send, expect and reject blocks."""
    for i, k in var_in_dict.items():
        frame.send["content"] = re.sub(i, k, frame.send["content"])
variable_replace.priority = 1

def store_regex(frame, regexes):
    """Capture regexes in responses and store in the storage dictionary. Accepts lists and strings."""
    def store_regex_single(frame, regex):
        match = re.search(regex, "".join(frame.responses))
        if match:
            frame.conman.storage[regex] = match.groups()
            frame.conman.message(1, "Regex \"" + regex + "\" captured: \"" + str(match.groups()) + "\"")
        else:
            frame.conman.terror("Expected regex \"" + regex + "\" not present in captured frame.")
    if isinstance(regexes, list):
        for regex in regexes:
            store_regex_single(frame, regex)
    elif isinstance(regexes, str):
        store_regex_single(frame, regexes)
store_regex.priority = 10

def check_regex(frame, regexes):
    """Verify that the regexes extracted in the current frame match those stored with store_regex.
    Regexes stored and retrieved based purely on the regex that's used to capture them."""
    def check_regex_single(frame, regex):
        match = re.search(regex, "".join(frame.responses))
        if match:
            if not (frame.conman.storage[regex] == match.groups()):
                frame.conman.terror("Mismatch between captured and stored data for regex " + regex + ".",
                                    "Stored: " + str(frame.conman.storage[regex]) +
                                    "\n Captured: " + str(match.groups))
            else:
                frame.conman.message(1, "Regex \"" + regex + "\" matches: \"" + str(match.groups()) + "\"")
        else:
            frame.conman.terror("Expected regex " + regex + "not present in captured frame.") 
    if isinstance(regexes, list):
        for regex in regexes:
            check_regex_single(frame, regex)
    else:
        check_regex_single(frame, regexes)
check_regex.priority = 12
