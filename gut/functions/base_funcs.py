import time

def timeout(frame, timeout):
    """Used to set the timeout variable, used by expect and expect_regex"""
    pass
timeout.priority = 0

def connect(frame):
    """Used to initiate the connection."""
    extrargs = []
    if hasattr(frame, "username"):
        extrargs.append(frame.username["username"])
    if hasattr(frame, "password"):
        extrargs.append(frame.password["password"])
    frame.connection = frame.conman.openconnection(frame.interface["interface"], frame.address["address"], *extrargs)     
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
address.required = True

def interface(frame, interface):
    """Used to set the connection interface. """
    pass
interface.priority = 0
interface.quiet = True
interface.required = True

def send(frame, content):
    frame.sendframe()
send.priority = 4
send.required = True

def capture(frame):
    frame.addresponse(frame.capturemessage())
capture.priority = 7
capture.required = True
capture.quiet = True
