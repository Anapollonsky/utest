#!/usr/bin/env python
import re
import time
import sys
import argparse
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
    """Include the YAML commands defined in another file. Works recursively, commands added in-place."""
    include_queue = pa.parse_yaml_file(thefile)
    command_queue[0].insert(0, (include_queue, thefile))
        
def parse_block(block, command_queue, conman):
    """Block-type dependent actions"""
    if "glo" in block: # Global settings being set
        ut.recursive_dict_merge(conman.glo, block["glo"])
    elif "inc" in block: # Inclusion of a file requested
        include_file(block["inc"], command_queue, conman)
    elif any([x in block for x in Conman.connfuncdict]): # new frame being defined
        for k in Conman.connfuncdict:
            if k in block:
                interface = k
        los = block[interface]
        los["interface"] = interface
        ut.recursive_dict_merge(los, conman.glo)
        frame = Frame.frameFromLos(conman, los)
        frame.perform_actions()        
 
def assign_function_attributes(conman):
    """Assign default attributes to all functions in gut_analyze.py"""
    functions = [method for name, method in an.__dict__.iteritems() if (callable(method) and hasattr(method, "priority"))]
    for func in functions:
        for attr in an.default_func_attrs:
            if not hasattr(func, attr):
                setattr(func, attr, an.default_func_attrs[attr])

def parse_command_queue (conman, queue):
    """Parse a "queue" (list,str) containing blocks to be executed and filename."""
    conman.message(3, "Entering \"" + queue[1] + "\"")
    while queue[0]:
        block = queue[0][0]
        del queue[0][0]        
        if isinstance(block, tuple):
            parse_command_queue(conman, block)
        else:
            parse_block(block, queue, conman)
    conman.message(3, "Leaving \"" + queue[1] + "\"")    
    
if __name__ == "__main__":
    args = parser.parse_args() 
    conman = Conman(args.verbose)
    conman.log = args.log
    assign_function_attributes(conman)

    iteration = 1
    while(iteration <= args.repeat):
        conman.message(4, "Beginning Iteration " + str(iteration) + " of " + str(args.repeat) + "...") 
        conman.glo = {}
        if args.address is not None:
            conman.glo["address"] = args.address
            
        command_queue = pa.parse_yaml_file(args.file)
        parse_command_queue(conman, (command_queue, args.file))

        conman.message(4, "Iteration " + str(iteration) + " Completed")
        iteration += 1
        
    conman.closeallconnections()
