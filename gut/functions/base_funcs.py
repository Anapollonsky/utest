import time

def timeout(frame, timeout):
    """Used to set the timeout variable, used by expect and expect_regex"""
    pass
timeout.priority = 0

def connect(frame):
    """Used to initiate the connection."""
    frame.connection = frame.conman.openconnection(frame) 
connect.priority = 1
connect.required = True
connect.quiet = True

def username(frame, username):
    """Used to set the connection username, if any."""
    pass
username.priority = 0
username.quiet = True

def password(frame, password):
    """Used to set the connection password, if any."""
    pass
password.priority = 0
password.quiet = True

def address(frame, address):
    """Used to set the connection address."""
    pass
address.priority = 0
address.quiet = True
address.required = False

def interface(frame, interface):
    """Used to set the connection interface. """
    pass
interface.priority = 0
interface.quiet = True
interface.required = True

# def shell(frame, shell):
#     """Used to set the connection username, if any."""
#     pass
# shell.priority = 0
# shell.quiet = True

def send(frame, content):
    """Send the frame."""
    frame.sendframe()
send.priority = 4
send.required = True

def capture(frame):
    """Capture some data."""
    test = frame.capturemessage()
    frame.addresponse(test)
capture.priority = 7
capture.required = True
capture.quiet = True
