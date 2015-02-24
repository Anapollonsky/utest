class Frame:
    """Representation of a sent/received frame."""
    
    def __init__(self, interface, send):
        self.interface = interface
        self.send = send
        self.wait = .5
        self.timeout = 10
        self.expect = []
        self.reject = []
        self.expect_regex = []
        self.reject_regex = []
        self.responses = []

    def addresponse(response):
        self.responses.append(response)


        
    def setwait(wait):
        self.wait = wait

    def settimeout(timeout):
        self.timeout = timeout

    def setexpect(expect):
        self.expect = expect
        
    def setexpect_regex(expect_regex):
        self.expect_regex = expect_regex

    def setreject(reject):
        self.reject = reject

    def setreject_regex(reject_regex):
        self.reject_regex = reject_regex
