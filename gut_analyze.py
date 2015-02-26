import time
import re
import pexpect
import gut_utils as ut

# active_functions = ["send", "reject", "reject_regex", "expect", "expect_regex", "wait_before",
#                     "wait_after", "timeout", "send_variable_replace"]

def send(frame, content):
    frame.conman.sendframe(frame)
send.priority = 4
send.defaults= {}

def reject(frame, array):
    """Throw an error if any string in list-argument is present in given frame's responses."""
    for capture in frame.responses:
        if any([re.search(k, capture) for k in [re.escape(x) for x in array]]):
            ut.notify("tf", "Captured rejected substring in response:\n" + k.strip() + "\nThe full response message is:\n" + "".join(frame.responses))
    ut.notify("update", "Test Passed")            
reject.priority = 8
reject.defaults = {}

def reject_regex(frame, array):
    """Throw an error if any regex in list-argument is present in given frame's responses."""
    for capture in frame.responses:
        if any([re.search(k, capture) for k in array]):
            ut.notify("tf", "Captured rejected regex substring in response:\n" + k.strip() + "\nThe full response message is:\n" + "".join(frame.responses))
    ut.notify("update", "Test Passed")
reject_regex.priority = 8
reject_regex.defaults = {}

def expect(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = [re.escape(x) for x in array]
    timer = frame.timeout if hasattr(frame, "timeout") else 10 
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        temp_expect.insert(0, pexpect.TIMEOUT)
        i = frame.connection.expect(temp_expect, timeout=timer)
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = frame.connection.before + frame.connection.after
        if i == 0:
            ut.notify("tf", "Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + ".")
        for k in diminishing_expect[:]:
            if re.search(k, capture):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            ut.notify("not", "Captured in response:\n" + k.strip())
        frame.addresponse(capture)
    ut.notify("update", "Test Passed")
expect.priority = 6
expect.defaults = {}

def expect_regex(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = array
    timer = frame.timeout if hasattr(frame, "timeout") else 10     
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        temp_expect.insert(0, pexpect.TIMEOUT)
        i = frame.connection.expect(temp_expect, timeout=timer)
        if i == 0:
            ut.notify("tf", "Timeout while waiting for the following regexes:\n" + str(diminishing_expect) + ".")
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = frame.connection.before + frame.connection.after            
        for k in diminishing_expect[:]:
            if re.search(k, capture):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            ut.notify("not", "Captured in response:\n" + k.strip())
        frame.addresponse(capture)
    ut.notify("update", "Test Passed")
expect_regex.priority = 6
expect_regex.defaults={}

def timeout(frame, timeout):
    """Used to set the timeout variable, used by expect and expect_regex"""
    pass
timeout.priority = 1
timeout.defaults = {}


def address(frame, address):
    """Used to set the connection address. If unused, set by other things."""
    pass
address.priority = 1
address.defaults = {}

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

def send_variable_replace(frame, var_in_dict):
    """Replaces all instances of one word with another in all sent messages."""
    outstr = str(frame.send["content"])
    for i, k in var_in_dict.items():
        outstr = re.sub(i, k, outstr)
    frame.send["content"] = outstr    
send_variable_replace.priority = 1
send_variable_replace.defaults = {}
