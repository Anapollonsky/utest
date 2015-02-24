#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
# from collections import deque
import yaml
from copy import deepcopy


# from gut_connections import *
# from utils import *
import utils as ut
from gut_connections import Conman
from gut_frame import Frame

VERSION = 1 

global glo, globase
global global_command_queue

los = {}
cons = ["sh",
        "bci",
        "ard546"]

sym = {"sh": "shcommand",
       "bci":"bcicommand",
       "ard546":"ard546command",
       "inc":"include",
       "glo":"global",
       "var":"variables",
       "rrej":"reject-regex",
       "rej":"reject",
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

globase= {sym["rrej"]: [],
          sym["rej"]: [],
          sym["expr"]: [],
          sym["exp"]: [],
          sym["wait"]: .2,
          sym["tout"]: 10}
glo = deepcopy(globase)

def sendrec(frame):
    global conn, board, sym
    tempconn = conn.sendframe(frame.interface, board, frame.send)
    diminishing_expect = frame.expect_regex + [re.escape(x) for x in frame.expect]
    captured_lines_global = []
    captured_lines_local = []
    timer = frame.timeout
    while diminishing_expect:
        iter_time = time.time()
        temp_expect = list(diminishing_expect)
        temp_expect.insert(0, pexpect.TIMEOUT)
        i = tempconn.expect(temp_expect, timeout=timer)
        timer = 10 - (time.time() - iter_time) # Subtract time it took to capture
        capture = tempconn.after
        if i == 0:
            ut.notify("tf", "Timeout while waiting for the following substrings:\n" + str(diminishing_expect) + "\nExiting.")
        if any([re.search(k, capture) for k in frame.reject_regex]):
            ut.notify("tf", "Captured rejected regex substring in response:\n" + k + "\nExiting.")
        if any([re.search(k, capture) for k in [re.escape(x) for x in frame.reject]]):
            ut.notify("tf", "Captured rejected substring in response:\n" + k + "\nExiting.")
        for k in diminishing_expect[:]:
            match = re.search(k, capture)
            captured_lines_local.append(k)
            captured_lines_global.append(k)            
            diminishing_expect.remove(k)
        for k in captured_lines_local:
            ut.notify("not", "Captured in response:\n" + k + "\n")
    time.sleep(frame.wait)

def parse_yaml_file(thefile):
    """Take a YAML file and parse it in such a way that the upper-most dictionary is instead saved as a list, for sequential access."""
    try:
        infile = open(thefile, 'r')
    except IOError:
        ut.notify("fatalerror", "Failed to open file " + thefile + ", exiting")
        
    yamlsplit = re.split("\n(?!\s)", infile.read().strip())
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#']
    return yamlparse
    
def include_file(thefile):
    """Include the YAML commands defined in another file. The commands are added in-place."""
    global global_command_queue
    ut.notify("not", "Including file " + thefile)
    include_queue = parse_yaml_file(thefile)
    global_command_queue.reverse()
    while include_queue:
        global_command_queue.append(include_queue.pop())
    global_command_queue.reverse()
        
def parse_block(block):
    """Depending on what kind of block is given, merge settings with globals and move to next stage."""
    global glo, board, sym
    if sym["glo"] in block:
        glo = deepcopy(globase)
        ut.recursive_dict_merge(glo, block[sym["glo"]])
    elif sym["inc"] in block:
        include_file(block[sym["inc"]])
    elif any([x in block for x in Conman.conncommdict.values()]):
        for k in Conman.conncommdict:
            if Conman.conncommdict[k] in block:
                interface = k
        print block
        los = block[Conman.conncommdict[interface]]
        los["interface"] = interface
        ut.recursive_dict_merge(los, glo)

        new_frame = Frame(interface, los[sym["send"]])
        new_frame.expect = los[sym["exp"]]
        new_frame.expect_regex = los[sym["expr"]]
        new_frame.reject = los[sym["rej"]]
        new_frame.reject_regex = los[sym["rrej"]]
        new_frame.wait = los[sym["wait"]]
        new_frame.timeout = los[sym["tout"]]        
        sendrec(new_frame)

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
    print args.verbose
    conn = Conman(args.verbose)
    board = args.board
    
    while global_command_queue:
        block = global_command_queue[0]
        del global_command_queue[0]
        parse_block(block)
        
    conn.closeallconnections()
