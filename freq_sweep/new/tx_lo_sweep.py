from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from N9020A_Interface import N9020A
from time import sleep
import datetime
from math import log
import csv
import re
import os
import argparse

VERSION = 1

## Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("band", help="hb/lb, highband or lowband")
parser.add_argument("tx", help="transmitter 1/2")
parser.add_argument("board", help="board address")
parser.add_argument("mxa", help="mxa address, expected model N9020A")
parser.add_argument("-s", "--step", help="step size, in hz", default = 1e6, type=float)
parser.add_argument("-b", "--bandwidth", help="bandwidth, in hz", default = 5e6, type=float)
parser.add_argument("-w", "--waveform", help="waveform filename" , default = "LTE_5MHz_1Carrier.bin")
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))

args = parser.parse_args() # Parse arguments

## Variable Configuration
band_info = {"lb": {
                 "lofreq": 700e6,
                 "hifreq": 900e6,
                 "srx_atten": 250, #5db
                 "txi_atten": 100, #5db
                 "txe_atten": 725,
             },
             "hb": {
                 "lofreq": 1710e6, 
                 "hifreq": 2.2e9,
                 "srx_atten": 255, #0db
                 "txi_atten": 100, #5db
                 "txe_atten": 0,
             }
}
board = args.board
mxaaddr = args.mxa
lofreq = band_info[args.band]["lofreq"] 
hifreq = band_info[args.band]["hifreq"]
step = args.step 
bandwidth = args.bandwidth 
waveform = args.waveform
timestamp =  datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = "tx_lo_sweep_%s_%s_%s_%s.csv" % (args.band, args.tx, args.board, timestamp)

srx_atten = band_info[args.band]["srx_atten"]
txi_atten = band_info[args.band]["txi_atten"]
txe_atten = band_info[args.band]["txe_atten"]

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxa = N9020A(mxaaddr) 
print("Connections established...")

## Setup
bci.set_output(False)
bci.set_output(True)


# Transmitter
# Note, set_atten indices are correct for DAS SW v94 and later.
bci.set_atten(8, srx_atten) # srx
if args.tx == "1":
    bci.set_tx_rf_switches(0, 3)
    bci.set_atten(1, txi_atten) # Internal TX1
    bci.set_atten(5, txe_atten) # External TX1
    bci.set_atten(0, 480)       # Max out Internal TX2
    bci.set_atten(4, 1023)      # Max out External TX2

elif args.tx == "2":
    bci.set_tx_rf_switches(0, 0)
    bci.set_atten(0, txi_atten) # Internal TX2
    bci.set_atten(4, txe_atten) # External TX2
    bci.set_atten(1, 480)       # Max out Internal TX1
    bci.set_atten(5, 1023)      # Max out External TX1

# Lock
bci.set_lo(0, lofreq)
assert bci.ensure_reference_pll_lock("EXT", 1)
print("Board configured...")

# MXA Setup
mxa.do_jeff_mxa_setup()
print("MXA Configured...")

# Waveform
ftp.put(waveform, "/tmp/")
bci.do_tx_play_waveform("/tmp/" + waveform) 
print("Initial Setup Completed...")

print("Writing to " + csv_filename)
with open(csv_filename, 'w') as csvfile:
    ## CSV Header
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["tx_lo_sweep.py version: " + str(VERSION)])
    for member in [str(x) + ": " + str(y) for (x, y) in vars(args).items()]: # extract arguments, put in .csv file
        csvwriter.writerow([member])
    csvwriter.writerow(["SRX Attenuation: " + str(srx_atten)])
    csvwriter.writerow(["TX Internal Attenuation: " + str(txi_atten)])
    csvwriter.writerow(["TX External Attenuation: " + str(txe_atten)])
    csvwriter.writerow([])
    csvwriter.writerow(["Frequency", "Channel Power", "readsrxpower", "Time-Domain Power",
                        "Freq-Domain Power", "Bandwidth Power"])

    # Data
    for freq in range(int(lofreq), int(hifreq) + 1, int(step)):
        filename = "srx_capture"
        bci.set_lo(0, freq)
        mxa.set_freq(freq)
        sleep(1)
        srxpower = bci.get_srx_power(0)
        chanpwr, _ = mxa.get_chanpwr_psd()

        ## Capture
        for k in range(3): # Prevent repetition of data
            bci.do_srx_capture("/tmp/" + filename)
        sh.sendline("rm -f " + filename)
        ftp.get("/tmp/" + filename)
        
        ## Octave
        sh.sendline("./das_capture_power.m %s 307.2 0 %d" % (filename, int(bandwidth/1e6)))
        capture = sh.expect("Power in region: .*\d+\.\d+")
        pwrtime, pwrfreq, regionpwr = re.search("RMS Power: (\-?\d+\.?\d*).*RMS Power: (\-?\d+\.?\d*).*region: (\-?\d+\.?\d*)", capture).groups()

        ## Bookkeeping
        row = [float(freq), float(chanpwr), float(srxpower), float(pwrtime), float(pwrfreq), float(regionpwr)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
