from copy import deepcopy
import sys
import time
import types
import re
import inspect
import operator
from time import sleep

class Interface(object):
    """Representation of a sent/received frame."""



class Interactive_Interface(Interface):
    """ Extension of Frame class that implements functions useful for generic
    conversations with the target """
    
    # def reject(self, array, regex = False):
    #     """Throw an error if any string in list-argument is present in given frame's responses."""
    #     if isinstance(array, list):
    #         if regex == True and any([re.search(k, self._response) for k in [str(x) for x in array]]):
    #             self.conman.terror(["Captured rejected regex in response:" + k.strip(), self._response])
    #         elif regex == False and any([x in self._response for x in array]):
    #             self.conman.terror(["Captured rejected substring in response:" + k.strip(), self._response])
    #     else:
    #         if regex == True and re.search(str(array), self._response):
    #             self.conman.terror(["Captured rejected regex in response:" + array.strip(), self._response])
    #         elif regex == False and str(array) in self._response:
    #             self.conman.terror(["Captured rejected substring in response:" + array.strip(), self._response])


    def echo(self, command, delay = 0):
        self.sendline(command)
        sleep(delay)
        return self.capture()
        
    def expect_all(self, array, regex = False, timeout = 10):
        """Expect to capture strings
        Tries to capture all members in an array of strings or regexes before time runs out"""
        if not isinstance(array, list): array = [array]
        if not regex: array = [re.escape(x) for x in array]
        timer = int(timeout)
        capture = ""
        while diminishing_expect:
            captured_lines_local = []
            iter_time = time.time()
            temp_expect = list(diminishing_expect)
            i = self.expect(temp_expect, timer)
            if i[1] == True:
                return diminishing_expect
            timer -= (time.time() - iter_time) # Subtract time it took to capture
            capture += i[0] # Captured Value
            for k in diminishing_expect[:]:
                if re.search(k, capture):
                    captured_lines_local.append(k)
                    diminishing_expect.remove(k)
        return capture

   
