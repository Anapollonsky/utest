class shframe(utestframe):

    def __init__(self, command):
        self.command = command

    @classmethod
    def spawnconnect(address):
        self.con = pexpect.spawn("telnet " + address)
        con.expect("ogin")
        con.sendline("lucent")
        con.expect("assword")
        con.sendline("password")
        
