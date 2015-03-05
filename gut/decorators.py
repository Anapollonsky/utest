def command(priority, hooks = {}):
    def decorator(func):
        func.priority = priority
        func.hooks = hooks
        return func
    return decorator
