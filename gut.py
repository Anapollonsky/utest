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
import gut_analyze as an
from gut_conman import Conman
from gut_frame import Frame

VERSION = 1 

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("file", help="ARD546 command list file")
parser.add_argument("-a", "--address", help="target address", default = None)
parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
parser.add_argument("-l", "--log", help="set output log filename", default = None)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))
    
def include_file(thefile, command_queue, conman):
    """Include the YAML commands defined in another file. The commands are added in-place."""
    conman.message(2, "Including file " + thefile)
    include_queue = pa.parse_yaml_file(thefile)
    command_queue.reverse()
    while include_queue:
        command_queue.append(include_queue.pop())
    command_queue.reverse()
        
def parse_block(block, global_config, command_queue, conman):
    """Block-type dependent actions"""
    if "glo" in block: # Global settings being set
        ut.recursive_dict_merge(global_config, block["glo"])
    elif "inc" in block: # Inclusion of a file requested
        include_file(block["inc"], command_queue, conman)
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
 
def assign_function_attributes(conman):
    """Assign default attributes to all functions in gut_analyze.py"""
    functions = [method for name, method in an.__dict__.iteritems() if (callable(method) and hasattr(method, "priority"))]
    for func in functions:
        for attr in an.default_func_attrs:
            if not hasattr(func, attr):
                setattr(func, attr, an.default_func_attrs[attr])
        
if __name__ == "__main__":
    args = parser.parse_args() 
    conman = Conman(args.verbose)
    conman.log = args.log
    assign_function_attributes(conman)

    iteration = 1
    while(iteration <= args.repeat):
        conman.message(4, "Beginning Iteration " + str(iteration) + " of " + str(args.repeat) + "...") 
        glo = {}
        if args.address is not None:
            glo["address"] = args.address
        global_command_queue = pa.parse_yaml_file(args.file)

        while global_command_queue:
            block = global_command_queue[0]
            del global_command_queue[0]
            glo = parse_block(block, glo, global_command_queue, conman)
        conman.message(4, "Iteration " + str(iteration) + " Completed")
        iteration += 1
        
    conman.closeallconnections()
