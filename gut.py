#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
# from collections import deque
import yaml
from copy import deepcopy

import utils as ut
from gut_connections import Conman
from gut_frame import Frame

VERSION = 1 

global glo, base_global_config
global global_command_queue

cons = ["sh",
        "bci",
        "ard546"]

# Symbol table
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
       "interface":"interface",
       "board":"board"}

# Command priority
builtinPriority = {"wait": 0,
                   "tout": 0,
                   "send": 1,
                   "expect": 2,
                   "reject": 2,
                   "expect-regex": 2,
                   "reject-regex": 2}

# Basic configuration
base_global_config= {sym["rrej"]: [],
                     sym["rej"]: [],
                     sym["expr"]: [],
                     sym["exp"]: [],
                     sym["wait"]: .2,
                     sym["tout"]: 10,
                     sym["board"]: "not_a_valid_board"}

glo = deepcopy(base_global_config)

# Parse command-line arguments
parser = argparse.ArgumentParser()    
parser.add_argument("board", help="board address")
parser.add_argument("file", help="ARD546 command list file")
parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))


def sendrec(frame):
    global conman, sym
    conman.sendframe(frame)
    frame.handle_responses()

def parse_yaml_file(thefile):
    """Take a YAML file and parse it in such a way that the upper-most dictionary is instead saved as a list, for sequential access."""
    try:
        infile = open(thefile, 'r')
    except IOError:
        ut.notify("fatalerror", "Failed to open file " + thefile + ", exiting")
        
    yamlsplit = re.split("\n(?!\s)", infile.read().strip())
    yamlparse = [yaml.load(x) for x in yamlsplit if x[0] != '#']
    return yamlparse
    
def include_file(thefile, command_queue):
    """Include the YAML commands defined in another file. The commands are added in-place."""
    ut.notify("not", "Including file " + thefile)
    include_queue = parse_yaml_file(thefile)
    command_queue.reverse()
    while include_queue:
        command_queue.append(include_queue.pop())
    command_queue.reverse()
        
def parse_block(block, global_config, command_queue):
    """Depending on what kind of block is given, merge settings with globals and move to next stage."""
    global sym, conman
    if sym["glo"] in block:
        ut.recursive_dict_merge(global_config, block[sym["glo"]])
    elif sym["inc"] in block:
        include_file(block[sym["inc"]], command_queue)
    elif any([x in block for x in Conman.conncommdict.values()]):
        for k in Conman.conncommdict:
            if Conman.conncommdict[k] in block:
                interface = k
        los = block[Conman.conncommdict[interface]]
        los["interface"] = interface
        ut.recursive_dict_merge(los, global_config)

        frame = Frame(los[sym["send"]])
        frame.expect = los[sym["exp"]]
        frame.expect_regex = los[sym["expr"]]
        frame.reject = los[sym["rej"]]
        frame.reject_regex = los[sym["rrej"]]
        frame.wait = los[sym["wait"]]
        frame.timeout = los[sym["tout"]]
        frame.connection = conman.openconnection(los[sym["interface"]], los[sym["board"]])
        sendrec(frame)
    return global_config

if __name__ == "__main__":
    args = parser.parse_args()
    base_global_config[sym["board"]] = args.board
    glo = deepcopy(base_global_config)
    global_command_queue = parse_yaml_file(args.file)
    global conman
    conman = Conman(args.verbose)
    
    while global_command_queue:
        block = global_command_queue[0]
        del global_command_queue[0]
        glo = parse_block(block, glo, global_command_queue)
        
    conman.closeallconnections()
