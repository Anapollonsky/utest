import sys

def notify(level, message):
    """Perform formatting of output based on level parameter."""
    if level == "bas": # basic message
        print("\n" + message)
    elif level == "not": # special notification
        print("\n> " + message)
    elif level == "tf": # Test Failure
        print("\n###" + message + "###")
        sys.exit()        
    elif level == "fe": # fatal error
        print("\n>>> " + message + " <<<")
        sys.exit()


# http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
def recursive_dict_merge(a, b):
    "merges b into a, performing dumb merge of list. (Don't nest dicts in lists!). a has priority."
    if isinstance(a, dict) and isinstance(b, dict):
        for key in b:
            if key in a:
                if (isinstance(a[key], dict) and isinstance(b[key], dict)) or (isinstance(a[key], list) and isinstance(b[key], list)):
                    recursive_dict_merge(a[key], b[key])
                else:
                    pass # if identical singles or different, a stays same
            else:
                a[key] = b[key]
    elif isinstance(a, list) and isinstance(b, list):
        for k in b:
            a.append(k)
    else:
        print("Merge error! " + str(a) + str(b))
        sys.exit()
    return a
    
