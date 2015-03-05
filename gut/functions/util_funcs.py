from time import gmtime, strftime

def variable_replace(frame, var_def):
    """Replaces all instances of one word with another in all send, expect and reject blocks."""
    for i, k in var_defs.items():
        if hasattr(frame, "send"):
            frame.send["content"] = re.sub(i, k, frame.send["content"])
        if hasattr(frame, "expect"):
            for member in frame.expect["array"]: 
                member = re.sub(i, k, member)
        if hasattr(frame, "expect_regex"):
            for member in frame.expect_regex["array"]:
                member = re.sub(i, k, member)
        if hasattr(frame, "reject"):
            for member in frame.reject["array"]:
                member = re.sub(i, k, member)
        if hasattr(frame, "reject_regex"):
            for member in frame.reject_regex["array"]:
                member = re.sub(i, k, member)                        
variable_replace.priority = 1

def print_time(frame, formatting="%H:%M:%S"):
    """High-priority time-print function. Optional argument specifies formatting."""
    frame.conman.message(1, strftime(formatting, gmtime()))
print_time.priority = 0

def print_response(frame):
    """Low-priority function that prints the captured response to the sent message."""
    frame.conman.message(1, "\n" + str(frame.responses) + "\n")
print_response.priority = 100    


def print_send(frame):
    """Low-priority function that prints the sent message."""
    frame.conman.message(1, "\n" + str(frame.send["content"]) + "\n")
print_send.priority = 100    


def log(frame, filename):
    """Low-priority function to log the sent and received messages to a given file."""
    try:
        infile = open(filename, 'a')
    except IOError:
        frame.conman.ferror("Failed to open file " + filename + " for logging.")
    infile.write(frame.send["content"] + "\n\n" + frame.responses + "\n\n")
    infile.close()
log.priority = 100
log.quiet = True
