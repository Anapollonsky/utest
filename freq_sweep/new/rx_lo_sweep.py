from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from N5180_Interface import N5180
from time import sleep
import datetime
from math import log
import csv
import re
import os
import argparse

VERSION = 3

## Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("band", help="hb/lb, highband or lowband")
parser.add_argument("rx", help="receiver 1/2")
parser.add_argument("board", help="board address")
parser.add_argument("mxg", help="mxg address, expected model N5180")
parser.add_argument("-s", "--step", help="step size, in hz", default = 1e6, type=float)
parser.add_argument("-b", "--bandwidth", help="bandwidth, in hz", default = 5e6, type=float)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))

args = parser.parse_args() # Parse arguments

## Variable Configuration
band_info = {"lb": {
                 "lofreq": 700e6,
                 "hifreq": 900e6,
                 "rx_atten": 255 
             },
             "hb": {
                 "lofreq": 1710e6, 
                 "hifreq": 2.2e9,
                 "rx_atten": 255
             }
}
board = args.board
mxgaddr = args.mxg
lofreq = band_info[args.band]["lofreq"] 
hifreq = band_info[args.band]["hifreq"]
step = args.step 
bandwidth = args.bandwidth 
timestamp =  datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = "rx_lo_sweep_%s_%s_%s_%s.csv" % (args.band, args.rx, args.board, timestamp)

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxg = N5180(mxgaddr) 
print("Connections established...")

## Setup

# Transmitter
rx_atten = band_info[args.band]["rx_atten"]
bci.set_atten(10, rx_atten) 
bci.set_atten(11, rx_atten) 

# Capture filename
pid = os.getpid()
filename = "rx_capture" + str(pid)
    
# Lock
bci.set_lo(2, lofreq)
assert bci.ensure_reference_pll_lock("EXT", 1)
print("Board configured...")

# MXG Setup
mxg.set_power(20)
mxg.set_output(True)
print("MXG Configured...")


print("Initial Setup Completed...")

print("Writing to " + csv_filename)
with open(csv_filename, 'w') as csvfile:
    ## CSV Header
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["tx_lo_sweep.py version: " + str(VERSION)])
    for member in [str(x) + ": " + str(y) for (x, y) in vars(args).items()]: # extract arguments, put in .csv file
        csvwriter.writerow([member])
    csvwriter.writerow(["RX Attenuation: " + str(rx_atten)])
    csvwriter.writerow([])
    csvwriter.writerow(["Frequency", "readrxpower", "Time-Domain Power",
                        "Freq-Domain Power", "Bandwidth Power"])

    # Data
    for freq in range(int(lofreq), int(hifreq) + 1, int(step)):
        bci.set_lo(2, freq)
        mxg.set_freq(freq)
        sleep(2)
        rxpower = bci.get_rx_power(1, 1, bandwidth)

        ## Capture
        sh.sendline("rm -f " + filename)
        for k in range(3): # Prevent repetition of data
            bci.do_rx_capture("/tmp/" + filename, args.rx)
        ftp.get("/tmp/" + filename)
        
        ## Octave
        sh.sendline("./das_capture_power.m %s 307.2 0 %d" % (filename, int(bandwidth/1e6)))
        capture = sh.expect("Power in region: .*\d+\.\d+")
        pwrtime, pwrfreq, regionpwr = re.search("RMS Power: (\-?\d+\.?\d*).*RMS Power: (\-?\d+\.?\d*).*region: (\-?\d+\.?\d*)", capture).groups()

        ## Bookkeeping
        row = [float(freq), float(rxpower), float(pwrtime), float(pwrfreq), float(regionpwr)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
