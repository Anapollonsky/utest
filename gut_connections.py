import utils
import sys

class gut_connections:
    connections = []

    def ard546connect(address):
        return pexpect.spawn("telnet " + address + " 1307")

    def bciconnect(address):
        return pexpect.spawn("telnet " + address + " 7006")    

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


    def openconnection(self, interface, address):
        conn = conndict[interface](address)
        if conn:
            notify("Connected to " + interface + " at " + address, message)
        conn.address = address
        conn.interface = interface

        connections.append(conn)
        return conn

    def sendframe(self, interface, address, content):
        for connection in connections:
            if connection.address == address and connection.interface == interface:
                connection.sendline(content)
                return connection
        connection = openconnection(self, interface, address)
        connection.sendline(content)
        
        return connection
                  
    def sendframe(self, connection, content):
        connection.sendline(content)
        return connection

    def closeconnection(self, interface, address):
        for connection in connections:
            if connection.address == address and connection.interface == interface:
                connection.close()
            del connection
        notify("Connection to " + interface + " at " + address + "not found! Exiting.", "error")
        sys.exit()

    def closeconnection(self, connection):
        connection.close()
        del connection

