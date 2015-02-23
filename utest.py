#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
# from collections import deque
import yaml
from copy import deepcopy


from gut_connections import *
# from utils import *
import utils as ut
import parser_functions as pf

VERSION = 1

global glo, globase
global global_command_queue

los = {}
cons = ["sh",
        "bci",
        "ard546"]
sym = {"sh": "shcommand",
       "bci":"bcicommand",
       "546":"ard546command",
       "inc":"include",
       "glo":"global",
       "var":"variables",
       "rreg":"reject-regex",
       "reg":"reject",
       "expr":"expect-regex",
       "exp":"expect",
       "send":"send",
       "wait":"wait",
       "tout":"timeout",
       "interface":"interface"}

builtinPriority = {"wait": 0,
                   "tout": 0,
                   "send": 1,
                   "expect": 2,
                   "reject": 2,
                   "expect-regex": 2,
                   "reject-regex": 2}

globase= {sym["rreg"]: [],
          sym["reg"]: [],
          sym["expr"]: [],
          sym["exp"]: [],
          sym["wait"]: .2,
          sym["tout"]: 10}
glo = deepcopy(globase)

def sendrec(los):
    global conn, board, sym
    tempconn = conn.sendframe(los[sym["interface"]], board, los[sym["send"]])
    diminishing_expect = los[sym["expr"]]
    captured_lines_global = []
    captured_lines_local = []
    timer = los[sym["tout"]]
    while diminishing_expect:
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        temp_expect.insert(0, pexpect.TIMEOUT)
        i = tempconn.expect(temp_expect, timeout=timer)
        timer = 10 - (time.time() - iter_time) # Subtract time it took to capture
        capture = tempconn.after
        if i == 0:
            ut.notify("tf", "Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + "\nExiting.")
        if any([re.search(k, capture) for k in los[sym["rreg"]]]):
            ut.notify("tf", "Captured rejected substring in response:\n" + k + "\nExiting.")
        for k in diminishing_expect[:]:
            match = re.search(k, capture)
            captured_lines_local.append(k)
            captured_lines_global.append(k)            
            diminishing_expect.remove(k)
        for k in captured_lines_local:
            ut.notify("not", "Captured in response:\n" + k + "\n")
    time.sleep(los[sym["wait"]])

def parse_yaml_file(thefile):
    try:
        infile = open(thefile, 'r')
    except IOError:
        ut.notify("fatalerror", "Failed to open file " + thefile + ", exiting")
        
    yamlsplit = re.split("\n(?!\s)", infile.read().strip())
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#']
    return yamlparse
    
def include_file(thefile):
    global global_command_queue
    ut.notify("not", "Including file " + thefile)
    include_queue = parse_yaml_file(thefile)
    global_command_queue.reverse()
    while include_queue:
        global_command_queue.append(include_queue.pop())
    global_command_queue.reverse()
        
def parse_block(block):
    global glo, board, sym
    if sym["glo"] in block:
        glo = deepcopy(globase)
        ut.recursive_dict_merge(glo, block[sym["glo"]])
    elif sym["inc"] in block:
        include_file(block[sym["inc"]])
    elif sym["bci"] in block:
        los = block[sym["bci"]]
        los[sym["interface"]] = "bci"
        ut.recursive_dict_merge(los, glo)
        sendrec(los)
    elif sym["sh"] in block:
        los = block[sym["sh"]]
        los[sym["interface"]] = "sh"
        ut.recursive_dict_merge(los, glo)
        sendrec(los)        
    elif sym["546"] in block:
        los = block[sym["546"]]
        los[sym["interface"]] = "ard546"
        ut.recursive_dict_merge(los, glo)
        sendrec(los) 

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

    global_command_queue = parse_yaml_file(args.file)

    global conn
    global board
    conn = gut_connections()
    board = args.board
    
    while global_command_queue:
        block = global_command_queue[0]
        del global_command_queue[0]
        parse_block(block)
        
    conn.closeallconnections()
