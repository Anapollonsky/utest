def command(priority, hooks = {}, quiet = False):
    def decorator(func):
        func.priority = priority
        func.hooks = hooks
        func.quiet = quiet
        return func
    return decorator

def hook(hook = True):
    def decorator(func):
        func.hook = True
        return func
    return decorator
