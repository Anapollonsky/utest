import utils as ut
import sys
import pexpect

class Conman:
    """Class responsible for managing pexpect connections and different frame types."""
    connections = []
    
    def __init__(self, trace):
        self.trace_level = trace

    ## Connection list        
    def ard546connect(address):
        return pexpect.spawn("telnet " + address + " 1307")

    def bciconnect(address):
        con = pexpect.spawn("telnet " + address + " 7006")
        con.expect("ogin")
        con.sendline("lucent")
        con.expect("assword")
        con.sendline("password")
        return con

    def shconnect(address):
        con = pexpect.spawn("telnet " + address)
        con.expect("ogin")
        con.sendline("lucent")
        con.expect("assword")
        con.sendline("password")
        return con

    connfuncdict = {
         "ard546": ard546connect
        ,"sh": shconnect
        ,"bci": bciconnect
    }

    conncommdict = {
         "ard546": "ard546command"
        ,"sh": "shcommand"
        ,"bci": "bcicommand"
    }
    
    ## Connection Management    
    def openconnection(self, interface, address):
        conn = Conman.connfuncdict[interface](address)
        if conn:
            ut.notify("message", "Connected to " + interface + " at " + address)
        conn.address = address
        conn.interface = interface
        if self.trace_level == 3:
            conn.logfile_read = sys.stdout
        Conman.connections.append(conn)
        return conn

    def sendframe(self, interface, address, content):
        for connection in Conman.connections:
            if connection.address == address and connection.interface == interface:
                connection.sendline(content)
                return connection
        connection = self.openconnection(interface, address)
        connection.sendline(content)
        return connection

    def closeconnection(self, connection):
        connection.close()
        del connection

    def closeallconnections(self):
        for connection in Conman.connections:
            connection.close()
            del connection
