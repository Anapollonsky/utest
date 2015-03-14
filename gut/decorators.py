def command(priority, hooks = {}, quiet = False):
    def decorator(func):
        func.priority = priority
        func.hooks = hooks
        func.quiet = quiet
        func.derived = False
        return func
    return decorator

def hook(hook = True):
    def decorator(func):
        func.hook = True
        return func
    return decorator


# def bind(f):
#     """Decorate function `f` to pass a reference to the function
#     as the first argument"""
#     return f.__get__(f, type(f))

# @bind
# def foo(self, x):
#     "This is a bound function!"
#     print(self, x)
