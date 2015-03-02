
from time import gmtime, strftime
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

def print_time(frame, formatting="%H:%M:%S"):
    """High-priority time-print function. Optional argument specifies formatting."""
    frame.conman.message(1, strftime(formatting, gmtime()))
print_time.priority = 0

def log(frame, filename):
    try:
        infile = open(filename, 'a')
    except IOError:
        conman.ferror("Failed to open file " + thefile + " for logging.")
    infile.write(frame.send["content"] + "\n\n" + frame.responses)        
log.priority = 100
log.quiet = True
