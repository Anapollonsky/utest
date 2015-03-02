## Import functions from external files here.
from base_funcs import *
from regex_funcs import *

# Describe the default attributes of functions. These are used for all functions if not otherwise
# explicitly set. Priority is excluded because a function without a defined priority cannot be run.
default_func_attrs = {"defaults":{}, "quiet": False}

################################################################################
## Function definitions go below this line. Keep it neat.

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
        if hasattr(frame, "send"):
            frame.send["content"] = re.sub(i, k, frame.send["content"])
        if hasattr(frame, "expect"):
            for member in frame.expect["array"]: 
                member = re.sub(i, k, member)
        if hasattr(frame, "expect_regex"):
            for member in frame.expect_regex["array"]:
                member = re.sub(i, k, member)        
variable_replace.priority = 1
