import time
import pexpect
import re
import utils as ut
        
class Frame:
    """Representation of a sent/received frame."""
    
    def __init__(self, send):
        self.send = send
        self.wait = .5
        self.timeout = 10
        self.expect = []
        self.reject = []
        self.expect_regex = []
        self.reject_regex = []
        self.responses = []

    def addresponse(self, response):
        self.responses.append(response)

    def handle_responses(self):
        diminishing_expect = self.expect_regex + [re.escape(x) for x in self.expect]
        captured_lines_local = []
        timer = self.timeout
        while diminishing_expect:
            iter_time = time.time()
            temp_expect = list(diminishing_expect)
            temp_expect.insert(0, pexpect.TIMEOUT)
            i = self.connection.expect(temp_expect, timeout=timer)
            timer = 10 - (time.time() - iter_time) # Subtract time it took to capture
            capture = self.connection.after
            if i == 0:
                ut.notify("tf", "Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + "\nExiting.")
            if any([re.search(k, capture) for k in self.reject_regex]):
                ut.notify("tf", "Captured rejected regex substring in response:\n" + k + "\nExiting.")
            if any([re.search(k, capture) for k in [re.escape(x) for x in self.reject]]):
                ut.notify("tf", "Captured rejected substring in response:\n" + k + "\nExiting.")
            for k in diminishing_expect[:]:
                if re.search(k, capture):
                    captured_lines_local.append(k)
                    diminishing_expect.remove(k)
            for k in captured_lines_local:
                ut.notify("not", "Captured in response:\n" + k + "\n")
            self.addresponse(capture)
        time.sleep(self.wait)

    
