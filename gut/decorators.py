def command(priority, hooks = {}, quiet = False):
    """ Mark a function as being a command function """
    def decorator(func):
        func.priority = priority
        func.hooks = hooks
        func.quiet = quiet
        func.derived = False
        return func
    return decorator

def hook(hook = True):
    """ Mark a function as being an argument hook """
    def decorator(func):
        func.hook = True
        return func
    return decorator
