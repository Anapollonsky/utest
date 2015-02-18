class bciframe(utestframe):

    def __init__(self, command):
        separated = command.strip().split(" ")
        self.command = separated[0]
        self.args = separated[1:]
        
    @classmethod
    def spawnconnect(address):
        self.con = pexpect.spawn("telnet " + address + " 7006")
