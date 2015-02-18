#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
import csv
from copy import deepcopy
import yaml

VERSION = 1
ARD546_PORT = "1307"

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser()    
    parser.add_argument("board", help="board address")
    parser.add_argument("file", help="ARD546 command list file")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
    parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
    parser.add_argument("--version", help="print out version and exit",
                        action='version', version='%(prog)s ' + str(VERSION))
    args = parser.parse_args()

    

    
    board_connect_command = "telnet " + args.board + " " + ARD546_PORT
    if args.verbose == 1 or args.verbose >= 3:
        print("Connecting with \"" + board_connect_command + "\"...") 
    con = pexpect.spawn(board_connect_command)
    if args.verbose > 1:
        con.logfile_read = sys.stdout
        i = con.expect(['login', pexpect.TIMEOUT], timeout=10)
    if i == 1:
        print("Failed to establish a connection with \"" +
              board_connect_command + "\". Exiting.")
        sys.exit()

        
