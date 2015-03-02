def timeout(frame, timeout):
    """Used to set the timeout variable, used by expect and expect_regex"""
    pass
timeout.priority = 0

def address(frame, address):
    """Used to set the connection address."""
    pass
address.priority = 0
address.quiet = True

def interface(frame, interface):
    """Used to set the connection interface. """
    pass
interface.priority = 0
interface.quiet = True

def send(frame, content):
    frame.sendframe()
send.priority = 4

