class ard546frame(utestframe):

    def __init__(self, command):
        self.command = command
        frametyperegex = re.search("MESSAGE\s*:\s*TYPE\s*=\s*(\w+)")
        self.frametype = frametyperegex.group(1)

        
