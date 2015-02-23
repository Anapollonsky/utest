class bciframe(utestframe):

    def __init__(self, command, connection):
        separated = command.strip().split(" ")
        self.command = separated[0]
        self.args = separated[1:]
        self.conn = connection
        
