#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
# from collections import deque
from copy import deepcopy

import gut_parser as pa
import gut_utils as ut
from gut_connections import Conman
from gut_frame import Frame

VERSION = 1 

global glo, base_global_config
global global_command_queue

# Parse command-line arguments
parser = argparse.ArgumentParser()    
parser.add_argument("board", help="board address")
parser.add_argument("file", help="ARD546 command list file")
parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))
    
def include_file(thefile, command_queue):
    """Include the YAML commands defined in another file. The commands are added in-place."""
    ut.notify("not", "Including file " + thefile)
    include_queue = pa.parse_yaml_file(thefile)
    command_queue.reverse()
    while include_queue:
        command_queue.append(include_queue.pop())
    command_queue.reverse()
        
def parse_block(block, global_config, command_queue):
    """Block-type dependent actions"""
    global conman
    if "glo" in block: # Global settings being set
        ut.recursive_dict_merge(global_config, block["glo"])
    elif "inc" in block: # Inclusion of a file requested
        include_file(block["inc"], command_queue)
    elif any([x in block for x in Conman.conncommdict.values()]): # new frame being defined
        for k in Conman.conncommdict:
            if Conman.conncommdict[k] in block:
                interface = k
        los = block[Conman.conncommdict[interface]]
        los["interface"] = interface
        ut.recursive_dict_merge(los, global_config)
        frame = Frame.frameFromLos(conman, los)
        frame.perform_actions()        
    return global_config

if __name__ == "__main__":
    args = parser.parse_args()
    glo = {}
    glo["board"] = args.board    
    global_command_queue = pa.parse_yaml_file(args.file)

    global conman 
    conman = Conman(args.verbose)
    
    while global_command_queue:
        block = global_command_queue[0]
        del global_command_queue[0]
        glo = parse_block(block, glo, global_command_queue)
        
    conman.closeallconnections()
