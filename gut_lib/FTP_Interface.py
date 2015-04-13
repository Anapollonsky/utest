import time
import os
from ftplib import FTP as low_FTP
import ntpath
from Interface import Interface


class FTP(Interface):
    
    def connect(self, address, username = None, password = None):
        """ Connection procedure for remote shell."""
        try:
            con = low_FTP(address, timeout = 10)
            con.login(username, password)
        except:
            print("boo")
            return None
        self._address = address
        self._username = username
        self._password = password
        self._connection = con
        
    __init__ = connect

    def close():
        self._connection.close()
        
########## Command functions

    def rcwd(self, directory):
        """ Change working directory on target. """
        self._connection.cwd(directory)
           
    def lcwd(self, directory):
        """ Change local working directory. """
        os.chdir(directory)
        
    def put(self, filename, destination = ""):
        """Transfer a file to the server. Binary mode by default."""
        self._connection.storbinary("STOR " + destination + filename, open(ntpath.basename(filename), "rb")) 

    def get(self, filename):
        """Transfer a file from the server. Binary mode by default."""
        self._connection.retrbinary("RETR " + filename, open(ntpath.basename(filename), "wb").write) 
