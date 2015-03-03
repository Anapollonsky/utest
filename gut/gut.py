#!/usr/bin/env python
import re
import time
import sys
import argparse
import sys
import yaml_parser as pa
import utils as ut
import functions.functions as fu
from conman import Conman
from frame import Frame
from copy import deepcopy

VERSION = 1 

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", help="ARD546 command list file", default = None)
parser.add_argument("-a", "--address", help="target address", default = None)
parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
parser.add_argument("-l", "--log", help="set output log filename", default = None)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))
    
def parse_include(thefile, command_queue, conman):
    """Include the YAML commands defined in another file. Works recursively, commands added in-place."""
    try:
        infile = open(thefile, 'r')
    except IOError:
        conman.ferror("Failed to open file " + thefile + ", exiting")            
    include_queue = pa.parse_yaml(infile, conman)
    command_queue[0].insert(0, (include_queue, thefile))

def parse_global(settings, conman):
    """Generate new global_temporary settings from global_permanent settings and new "global" block"""
    conman.global_temporary = deepcopy(conman.global_permanent)
    ut.recursive_dict_merge(conman.global_temporary, settings)

def parse_command(local_settings, conman):
    """Generate new local settings from global_temporary settings and new "cmd" block. Perform command actions."""
    ut.recursive_dict_merge(local_settings, conman.global_temporary)
    frame = Frame.frameFromLocalSettings(conman, local_settings)
    frame.perform_actions()
    
def parse_block(block, command_queue, conman):
    """Delegate actions based on top-level block type."""
    if "global" in block: # Global settings being set
        parse_global(block["global"], conman)
    elif "include" in block: # Inclusion of a file requested
        parse_include(block["include"], command_queue, conman)
    elif "cmd" in block: # new frame being defined
        parse_command(block["cmd"], conman)
    else:
        conman.ferror("Unexpected top-level name \"" + block.keys()[0] + "\" encountered.")
 
def assign_function_attributes(conman):
    """Assign default attributes to all functions in functions.py"""
    functions = [method for name, method in fu.__dict__.iteritems() if (callable(method) and hasattr(method, "priority"))]
    for func in functions:
        for attr in fu.default_func_attrs:
            if not hasattr(func, attr):
                setattr(func, attr, fu.default_func_attrs[attr])

def parse_command_queue (conman, queue):
    """Parse a "queue" (list,str) containing blocks to be executed and filename. Works recursively, on nested 'queues'."""
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
    if args.file:
        instream = open(args.file)
    elif not sys.stdin.isatty():
        instream = sys.stdin
    else:
        conman.ferror("No input stream found.")
    command_queue_base = pa.parse_yaml(instream, conman)        

    assign_function_attributes(conman)
    if args.address:
        conman.global_permanent["address"] = args.address
    if args.log:
        conman.global_permanent["log"] = args.log
            
    iteration = 1
    while(iteration <= args.repeat):
        conman.message(4, "Beginning Iteration " + str(iteration) + " of " + str(args.repeat) + "...") 
        command_queue = list(command_queue_base)
        parse_command_queue(conman, (command_queue, args.file))
        conman.message(4, "Iteration " + str(iteration) + " Completed")
        iteration += 1
        
    conman.closeallconnections()
