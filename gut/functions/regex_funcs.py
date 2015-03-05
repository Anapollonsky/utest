import time
import re

def reject(frame, array):
    """Throw an error if any string in list-argument is present in given frame's responses."""
    if isinstance(array, list):
        if any([re.search(k, frame.responses) for k in [re.escape(str(x)) for x in array]]):
            frame.conman.terror(["Captured rejected substring in response:" + k.strip(), frame.responses])
    else:
        if re.search(re.escape(str(array)), frame.responses):
            frame.conman.terror(["Captured rejected regex substring in response:" + array.strip(), frame.responses])                            
reject.priority = 8

def reject_regex(frame, array):
    """Throw an error if any regex in list-argument is present in given frame's responses."""
    if isinstance(array, list):
        if any([re.search(str(k), frame.responses) for k in array]):
                frame.conman.terror(["Captured rejected regex substring in response:" + k.strip(), frame.responses])
    else:
        if re.search(str(array), frame.responses):
            frame.conman.terror(["Captured rejected regex substring in response:" + array.strip(), frame.responses]) 
reject_regex.priority = 8

def expect(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = [re.escape(x) for x in array]
    timer = frame.timeout["timeout"] if hasattr(frame, "timeout") else 10
    if hasattr(frame, "responses"):
        for k in diminishing_expect[:]:
            if re.search(k, frame.responses): 
                diminishing_expect.remove(k)        
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        i = frame.expectmessage(temp_expect, timer)
        if i[1] == True:
            frame.conman.terror(["Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + ".", frame.responses])        
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = i[0] # Captured value
        frame.addresponse(capture)        
        for k in diminishing_expect[:]:
            if re.search(k, frame.responses):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            frame.conman.message(1, "Captured in response: " + k.strip())
    frame.timeout = {"timeout": timer}
expect.priority = 6

def expect_regex(frame, array):
    """Try and capture everything in array before time runs out."""
    diminishing_expect = array
    timer = frame.timeout["timeout"] if hasattr(frame, "timeout") else 10
    if hasattr(frame, "responses"):
        for k in diminishing_expect[:]:
            if re.search(k, frame.responses):
                diminishing_expect.remove(k)            
    while diminishing_expect:
        captured_lines_local = [] 
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        i = frame.expectmessage(temp_expect, timer)
        if i[1] == True:
            frame.conman.terror(["Timeout while waiting for the following regexes:\n" + str(diminishing_expect) + ".", frame.responses])
        timer -= (time.time() - iter_time) # Subtract time it took to capture
        capture = i[0]
        for k in diminishing_expect[:]:
            if re.search(k, capture):
                captured_lines_local.append(k)
                diminishing_expect.remove(k)
        for k in captured_lines_local:
            frame.conman.message(1, "Captured in response: " + k.strip())
        frame.addresponse(capture)
    frame.timeout = {"timeout": timer}
expect_regex.priority = 6


def store_regex(frame, regexes):
    """Capture regexes in responses and store in the storage dictionary. Accepts lists and strings."""
    def store_regex_single(frame, regex):
        match = re.search(regex, frame.responses)
        if match:
            frame.conman.storage[regex] = match.groups()
            frame.conman.message(1, "Regex \"" + regex + "\" captured: \"" + str(match.groups()) + "\"")
        else:
            frame.conman.terror(["Expected regex \"" + regex + "\" not present in captured frame.", frame.responses])
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
        match = re.search(regex, frame.responses)
        if match:
            if not (frame.conman.storage[regex] == match.groups()):
                frame.conman.terror(["Mismatch between captured and stored data for regex \"" + regex + "\".",
                                     "Stored: " + str(frame.conman.storage[regex]) +
                                     "\nCaptured: " + str(match.groups())])
            else:
                frame.conman.message(1, "Regex \"" + regex + "\" matches: \"" + str(match.groups()) + "\"")
        else:
            print (frame.responses)
            frame.conman.terror(["Expected regex " + regex + " not present in captured frame.", frame.responses]) 
    if isinstance(regexes, list):
        for regex in regexes:
            check_regex_single(frame, regex)
    else:
        check_regex_single(frame, regexes)
check_regex.priority = 12
