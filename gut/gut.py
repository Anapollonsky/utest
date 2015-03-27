#!/usr/bin/env python
import argparse
import colorama
import yaml_parser as pa
import utils as ut
from collections import deque
from conman import Conman
from copy import deepcopy
from interfaces.frame import Frame

colorama.init()

VERSION = 3

# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("file", help="ARD546 command list file")
parser.add_argument("-v", "--verbose", help="increase output verbosity", default = 0, action="count")
parser.add_argument("-r", "--repeat", help="set repetitions", default = 1, type=int)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))

def parse_block(block, command_queue, conman):
    def parse_include(thefile, command_queue, conman):
        """Include the YAML commands defined in another file."""
        include_queue = command_queue_from_file(conman, block["include"])
        include_queue.reverse()
        command_queue.extendleft(include_queue)

    def parse_command(local_settings, conman):
        """Generate new local settings from global_temporary settings and new "cmd" block. Perform command actions."""
        # Construct appropriate frame based on interface
        interface = conman.get_interface(local_settings["interface"])
        frame = interface(local_settings, conman)
        frame.perform_actions()

    """Delegate actions based on top-level block type."""
    if "type" not in block:
        conman.ferror("Block with no specified type. Exiting.")
    elif block["type"] == "include": # Inclusion of a file requested
        parse_include(block["include"], command_queue, conman)
    elif block["type"] == "command": # new frame being defined
        block.pop("type")
        parse_command(block, conman)
    else:
        conman.ferror("Unexpected type \"" + block["type"] + "\" encountered.")

def command_queue_from_file(conman, filename):
    try:
        infile = open(filename, 'r')
    except IOError:
        conman.ferror("Failed to open file " + filename + ", exiting")

    file_contents = pa.parse_yaml(open(filename))

    if "do" in file_contents:
        return deque(file_contents["do"])
    else:
        return deque()
        
def parse_command_queue (conman, queue):
    """Parse a "queue" (list,str) containing blocks to be executed and filename. Works recursively, on nested 'queues'."""
    while queue:
        parse_block(queue.popleft(), queue, conman)

if __name__ == "__main__":
    args = parser.parse_args() # Parse arguments

    conman = Conman(args.verbose) # Make conman
    command_queue_base = command_queue_from_file(conman, args.file)
    iteration = 1
    while(iteration <= args.repeat):
        conman.message(4, "Beginning Iteration " + str(iteration) + " of " + str(args.repeat) + "...")
        parse_command_queue(conman, (deepcopy(command_queue_base)))
        conman.message(4, "Iteration " + str(iteration) + " Completed")
        iteration += 1

    conman.closeallconnections()
