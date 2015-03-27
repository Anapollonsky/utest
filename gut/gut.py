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
        try:
            infile = open(block["include"], 'r')
        except IOError:
            conman.ferror("Failed to open file " + block["include"] + ", exiting")
        data =infile.read() if not hasattr(conman,"global_yaml") else conman.global_yaml + infile.read()
        parsed_yaml = pa.parse_yaml(conman, data)
        if "do" in parsed_yaml:
            include_queue = deque(parsed_yaml["do"])
        else:
            include_queue = deque([])
        include_queue.reverse()
        command_queue.extendleft(include_queue)

    def parse_command(local_settings, conman):
        """Generate new local settings from global_temporary settings and new "cmd" block. Perform command actions."""
        # Construct appropriate frame based on interface
        interface = conman.get_interface(local_settings["interface"])
        frame = interface(local_settings, conman)
        frame.perform_actions()

    def parse_message(settings, conman):
        """Parse requests for messages to be printed. Overrides verbosity settings."""
        level = 3
        if "level" in settings:
            if settings["level"] not in range(1, 5):
                conman.ferror("Invalid message level, should be in [1-4]")
            else:
                level = settings["level"]
        if "message" not in settings:
            conman.ferror("No message specified")
        conman.message(level, settings["message"])

    """Delegate actions based on top-level block type."""
    if "type" not in block:
        conman.ferror("Block with no specified type. Exiting.")
    elif block["type"] == "include": # Inclusion of a file requested
        parse_include(block["include"], command_queue, conman)
    elif block["type"] == "command": # new frame being defined
        block.pop("type")
        parse_command(block, conman)
    elif block["type"] == "message":
        parse_message(block, conman)
    else:
        conman.ferror("Unexpected type \"" + block["type"] + "\" encountered.")
       
def parse_command_queue (conman, queue):
    """Parse a "queue" (list,str) containing blocks to be executed and filename. Works recursively, on nested 'queues'."""
    while queue:
        parse_block(queue.popleft(), queue, conman)

if __name__ == "__main__":
    args = parser.parse_args() # Parse arguments
    conman = Conman(args.verbose) # Make conman
    pa.init(conman, args.file) # Parser initialization 

    # Root file i/o
    try:
        infile = open(args.file, 'r')
    except IOError:
        conman.ferror("Failed to open file " + filename + ", exiting")

    members = pa.parse_yaml(conman, infile.read())
    infile.close()
    if "do" in members:
           command_queue_base = deque(members["do"]) 
    else:
           conman.ferror("No \"do\" block found!")

    # The actual work
    iteration = 1
    while(iteration <= args.repeat):
        conman.message(4, "Beginning Iteration " + str(iteration) + " of " + str(args.repeat) + "...")
        parse_command_queue(conman, (deepcopy(command_queue_base)))
        conman.message(4, "Iteration " + str(iteration) + " Completed")
        iteration += 1

    conman.closeallconnections()
