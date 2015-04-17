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
parser.add_argument("-o", "--output", help="output filename" , default = None)

args = parser.parse_args() # Parse arguments

## Constants
conman = Conman("loss_profiles.yml", "band_info.yml") # Manages connections and other global state
band_info = dict(conman.storage["band_info"][args.band])

## Variable Configuration
board = args.board
mxgaddr = args.mxg
lofreq = band_info["lofreq"] 
hifreq = band_info["hifreq"]
step = args.step 
bandwidth = args.bandwidth 
timestamp =  datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = args.output or "tx_lo_sweep_%s_%s_%s_%s.csv" % (args.band, args.tx, args.board, timestamp)
gain = 20

## Check that cable compensation entry exists
if not mxgaddr in conman.storage["loss_profiles_parsed"]:
    print("Cannot find loss profile, exiting.")
    sys.exit()

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxg = N5180(mxgaddr) 
print("Connections established...")

## Setup

# Transmitter
rx_atten = band_info["rx_atten"]
if args.rx == "1":
    bci.set_atten(10, rx_atten) 
    bci.set_atten(11, 235)
elif args.rx == "2":
    bci.set_atten(10, 235)
    bci.set_atten(11, rx_atten) 

# Capture filename
pid = os.getpid()
filename = "rx_capture" + str(pid)
    
# Lock
bci.set_lo(2, lofreq)
assert bci.ensure_reference_pll_lock("EXT", 1)
print("Board configured...")

# MXG Setup
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
        loss = "%0.2f" % conman.get_loss_at_freqs(freq, mxgaddr)[0]
        mxg.set_freq(freq)
        mxg.set_power(gain + loss)
        sleep(2)
        rxpower = bci.get_rx_power(1, 1, bandwidth)

        ## Capture
        sh.sendline("rm -f " + filename)
        for k in range(3): # Prevent repetition of data
            bci.do_rx_capture("/tmp/" + filename, args.rx)
        ftp.get("/tmp/" + filename)
        
        ## Octave
        pwrtime, pwrfreq, regionpwr = Conman.das_capture_power(sh, filename, 0, bandwidth)

        ## Bookkeeping
        row = [float(freq), float(rxpower), float(pwrtime), float(pwrfreq), float(regionpwr), float(loss)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
