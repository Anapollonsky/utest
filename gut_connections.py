import utils as ut
import sys
import pexpect

class gut_connections:

    connections = []

    
    def __init__(self):
        pass

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

    conndict = {
         "ard546": ard546connect
        ,"sh": shconnect
        ,"bci": bciconnect
    }

    ## Connection Management    
    def openconnection(self, interface, address):
        conn = gut_connections.conndict[interface](address)
        if conn:
            ut.notify("message", "Connected to " + interface + " at " + address)
        conn.address = address
        conn.interface = interface
        conn.logfile_read = sys.stdout
        gut_connections.connections.append(conn)
        return conn

    def sendframe(self, interface, address, content):
        for connection in gut_connections.connections:
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
        for connection in gut_connections.connections:
            connection.close()
            del connection
