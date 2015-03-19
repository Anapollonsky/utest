import time
import os
import inspect
from ftplib import FTP
import socket
import ntpath
from interfaces.frame import Frame
from decorators import command



class ftp_Frame(Frame):
    interfacename = "ftp"
    global_permanent = {"connect": None}
    
    def establish_connection(self, address, username = None, password = None):
        """ Connection procedure for remote shell."""
        try:
            
            con = FTP(address, timeout = 10)
            con.login(username, password)
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

    @command(0)
    def rcwd(self, directory):
        """ Change working directory on target. """
        # old_directory = self._connection.pwd()        
        self._connection.cwd(directory)
        # if repeat:
        #     newrcwd = self.deriveFunctionWithPriority(self.rcwd, self.rcwd, 100)
        #     self.insertFunction(newrcwd, {"directory": old_directory, "repeat": False})
            
    @command(0)
    def lcwd(self, directory):
        """ Change local working directory. """
        # old_directory = os.getcwd()
        os.chdir(directory)
        # if repeat:
        #     newlcwd = self.deriveFunctionWithPriority(self.lcwd, self.lcwd, 100)
        #     self.insertFunction(newlcwd, {"directory": old_directory, "repeat": False})        
        
    @command(4) 
    def put(self, filename, binary = True):
        """Transfer a file to the server. Binary mode by default."""
        if binary:
            self._connection.storbinary("STOR %s" % ntpath.basename(filename), open(filename, 'rb'))
        else:
            self._connection.storlines("STOR %s" % ntpath.basename(filename), open(filename, 'r'))            
        
    @command(5) 
    def get(self, filename, binary = True):
        """Transfer a file from the server. Binary mode by default."""
        if binary:        
            self._connection.retrbinary('RETR %s' % filename, open(filename, 'wb').write)
        else:
            self._connection.retrlines("RETR %s" % filename, open(filename, 'w').write) 
