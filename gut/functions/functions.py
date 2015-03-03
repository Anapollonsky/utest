## Import functions from external files here.
from base_funcs import *
from regex_funcs import *
from util_funcs import *

# Describe the default attributes of functions. These are used for all functions if not otherwise
# explicitly set. Priority is excluded because a function without a defined priority cannot be run.
default_func_attrs = {"defaults":{}, "quiet": False, "required": False}

################################################################################
## Function definitions go below this line. Keep it neat.

def wait_after(frame, wait_time):
    """Low-priority wait function"""
    time.sleep(wait_time)
wait_after.priority = 101
wait_after.defaults = {"wait_time":.2}

def wait_before(frame, wait_time):
    """High-priority wait function"""
    time.sleep(wait_time)
wait_before.priority = -1
wait_before.defaults = {"wait_time":.2}    

def wait_after_send(frame, wait_time):
    """High-priority wait function that waits right after sending the command"""
    time.sleep(wait_time)
wait_after_send.priority = 5
wait_after_send.defaults = {"wait_time":.2}
