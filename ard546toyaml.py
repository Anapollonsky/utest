#!/usr/bin/env python
import re
import copy
import yaml

infile = "../../tmplog_"
outfile = "../out.yaml"
re.DOTALL


parser = argparse.ArgumentParser()
parser.add_argument("file", help="file containing ARD546 commands to scrape")


## Populate dictionary of frames

frames = {"GETRESPONSE":[],
              "GET":[],
              "SETRESPONSE":[],
              "SET":[],
              "EVENT":[],
              "ACTION":[],
              "ACTIONACK":[]} 

filecontents = open(infile, 'r').read()
for frametype in frames:
    frames[frametype] = re.findall("\[.*" + frametype + " .*\]", filecontents)

## Match the frames with same ID together

pairs = {"GET":[],
         "SET":[],
         "ACTION":[]
         }


def getpairs(first, second):

    for frame in frames[first]:
        sid = re.search("TRANSACTION:\s*ID=(\d+)\s*", frame).group(1)
        for rframe in frames[second]:
            rid = re.search("TRANSACTION:\s*ID=(\d+)\s*", rframe).group(1)
            if sid == rid:
                pairs[first].append([frame, rframe, sid])
                break

getpairs("GET","GETRESPONSE")
getpairs("SET","SETRESPONSE")
getpairs("ACTION","ACTIONACK")

## Sort all pairs by transactionID:
def flattenpairs(pairs):
    """Returns a list of pairs"""
    outpairs = []
    for pairgroup in pairs:
        for pair in pairs[pairgroup]:
            outpairs.append(pair)
    return outpairs

sortedpairs = sorted(flattenpairs(pairs), key=lambda x: int(x[2]))
# replace pipes with newlines

def reformatsend(pair):
    newpair = copy.deepcopy(pair)
    x = 0
    newpair[x] = re.sub(" \| ", "\n",newpair[x])
    newpair[x] = re.sub("\[", "[\n", newpair[x])
    newpair[x] = re.sub("\]", "\n]", newpair[x])
    newpair[x] = re.sub("\n\n", "\n", newpair[x])
    return newpair

def reformatexpect(pair):
    newpair = copy.deepcopy(pair)
    x = 1
    newpair[x] = re.sub("-", "\-", newpair[x])
    return newpair


sortedpairs = [reformatsend(pair) for pair in sortedpairs]
sortedpairs = [reformatexpect(pair) for pair in sortedpairs]
print sortedpairs[0]
##Write out to YAML
framelist = [{"global": {"interface":"ard546"}}]

for pair in sortedpairs:
    framelist.append({"cmd":{"send": pair[0], "expect_regex": [pair[1]], "print_send": None}})

outwrite = open(outfile, "w")

for frame in framelist:
    yaml.dump(frame, outwrite)
