def command(priority, hooks = {}):
    def decorator(func):
        func.priority = priority
        func.hooks = hooks
        return func
    return decorator

def hook(hook = True):
    def decorator(func):
        func.hook = True
        return func
    return decorator
