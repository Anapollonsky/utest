#!/usr/bin/env python

import pexpect
import re
import time
import sys
import argparse
from collections import deque
import yaml
import pprint

from gut_connections import *
# from utils import *
import utils as ut
import parser_functions as pf

VERSION = 1

global glo
global global_command_queue
glo= {}
los = {}

cons = ["sh", "bci", "ard546"]
sym = {
        "sh": "shcommand"
       ,"bci": "bcicommand"
       ,"546":"ard546command"
       ,"inc":"include"
       ,"glo":"global"
       ,"var":"variables"
       ,"rreg":"reject-regex"
       ,"reg":"reject"
       ,"expr":"expect-regex"
       ,"exp":"expect"
       ,"send":"send"
       ,"wait":"wait"
       ,"tout":"timeout"
}
r
builtinPriority = {
     "wait": 0
    ,"tout": 0
    ,"send": 1
    ,"expect": 2
    ,"expect-regex": 2
    ,"reject": 2
    ,"rejext-regex": 2
    }

def parse_yaml_file(thefile):
    try:
        infile = open(thefile, 'r')
    except IOError:
        ut.notify("fatalerror", "Failed to open file " + thefile + ", exiting")
    yamlsplit = re.split("\n(?!\s)", infile.read().strip())
    yamlparse = deque([yaml.load(x) for x in yamlsplit])
    return yamlparse
    
def include_file(thefile):
    global global_command_queue
    ut.notify("not", "Including file " + thefile)    
    include_queue = parse_yaml_file(thefile)
    include_queue.reverse()
    # print (include_queue)
    for k in include_queue:
        global_command_queue.appendleft(k)
    
    
def parse_block(block):
    global glo
    if sym["glo"] in block:
        glo = block[sym["glo"]]
    elif sym["inc"] in block:
        include_file(block[sym["inc"]])
        # pass
    elif sym["bci"] in block:
        los = block[sym["bci"]]
        ut.recursive_dict_merge(los , glo)
    elif sym["sh"] in block:
        los = block[sym["sh"]]
        ut.recursive_dict_merge(los , glo)
    elif sym["546"] in block:
        los = block[sym["546"]]
        ut.recursive_dict_merge(los , glo)

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

    while global_command_queue:
        block = global_command_queue.popleft()
        parse_block(block)
