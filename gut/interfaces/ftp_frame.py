import time
import os
import ftplib
import socket
from frame import Frame
from decorators import command

class ftp_Frame(Frame):
    interfacename = "ftp"    

    def establish_connection(self, address, username = None, password = None, port = "21"):
        """ Connection procedure for remote shell."""
        try:
            con = FTP.FTP(address, timeout = 10).login(username, password)
        except:
            return None
        return con
    
################################################################################
#################### Command functions

    @command(0, quiet=True)
    def username(self, username):
        """Used to set the connection username, if any."""
        self._username = username        

    @command(0, quiet=True)
    def password(self, password):
        """Used to set the connection password, if any."""
        self._password = password

    @command(0, quiet=True)
    def address(self, address):
        """Used to set the connection address."""
        self._address = address

    @command(0, quiet=True)
    def port(self, port):
        """Used to set the connection port."""
        self._port = port

    @command(0)
    def rcwd(self, directory):
        """Change working directory on target for frame duration."""
        old_directory = self._connection.pwd()        
        self._connection.cwd(directory)
        self.insertFunctionWithPriority(self.rcwd, self.rcwd, {"directory": old_directory}, 100)

    @command(0)
    def lcwd(self, directory):
        """Change local working directory for frame duration."""
        old_directory = os.getcwd()
        os.chdir(directory)
        self.insertFunctionWithPriority(self.lcwd, self.lcwd, {"directory": old_directory}, 100)
        
    @command(4) 
    def put(self, filename, binary = True):
        """Transfer a file to the server. Binary mode by default."""
        if binary:
            self._connection.storbinary("STOR %s" % filename, open(filename, 'rb').read)
        else:
            self._connection.storlines("STOR %s" % filename, open(filename, 'r').read)            
        
    @command(5) 
    def get(self, filename, binary = True):
        """Transfer a file from the server. Binary mode by default."""
        if binary:        
            self._connection.retrbinary('RETR %s' % filename, open(filename, 'wb').write)
        else:
            self._connection.retrlines("STOR %s" % filename, open(filename, 'w').read) 
