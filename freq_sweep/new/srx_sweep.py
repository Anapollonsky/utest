from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from N9020A_Interface import N9020A
from time import sleep
from math import log
import csv
import re
import os
import argparse

## Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("band", help="hb/lb, highband or lowband")
parser.add_argument("tx", help="transmitter 1/2")
parser.add_argument("board", help="board address")
parser.add_argument("mxa", help="mxa address, expected model N9020A")
parser.add_argument("-s", "--step", help="step size, in hz", default = 1e6, type=float)
parser.add_argument("-b", "--bandwidth", help="bandwidth, in hz", default = 5e6, type=float)
parser.add_argument("-w", "--waveform", help="waveform filename" , default = "LTE_5MHz_1Carrier.bin")
args = parser.parse_args() # Parse arguments

## Variable Configuration
bands = {"lb": [717e6, 894e6],
         "hb": [1805e6, 2.2e9]}
board = args.board
mxaaddr = args.mxa
lofreq = bands[args.band][0] # Goes by 'step' from lofreq (inclusive) to highfreq (inclusive)
hifreq = bands[args.band][1]
step = args.step 
bandwidth = args.bandwidth 
waveform = args.waveform 
csv_filename = "srx_sweep_%s_%s_%s_%s.csv" % (args.band, args.tx, args.board, args.mxa)

srx_atten = 250 # 5dB
txi_atten = 100 # 5dB
txe_atten = 725 

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxa = N9020A(mxaaddr) 
print("Connections established...")

## Setup
bci.set_output(False)
bci.set_output(True)

# Attenuation
bci.set_atten(8, srx_atten) # srx
bci.set_atten(1, txi_atten) # Internal TX 
bci.set_atten(0, txi_atten)
bci.set_atten(4, txe_atten) # External TX
bci.set_atten(5, txe_atten)

# Transmitter
if args.tx == "1":
    bci.set_tx_rf_switches(0, 0)
elif args.tx == "2":
    bci.set_tx_rf_switches(0, 3)

# Lock
bci.set_lo(0, lofreq)
for x in range(3):
    bci.set_reference("EXT")
    sleep(2)
assert bci.ensure_pll_lock(1)
print("Board configured...")

# MXA Setup
mxa.do_jeff_mxa_setup()
print("MXA Configured...")

# Waveform
ftp.put(waveform, "/tmp/")
bci.do_tx_play_waveform("/tmp/" + waveform) 
print("Initial Setup Completed...")

with open(csv_filename, 'w') as csvfile:
    ## CSV Header
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow([str(x) + ": " + str(y) for (x, y) in vars(args).items()]) # extract arguments, put in .csv file
    csvwriter.writerow(["SRX Attenuation: " + str(srx_atten)])
    csvwriter.writerow(["TX Internal Attenuation: " + str(txi_atten)])
    csvwriter.writerow(["TX External Attenuation: " + str(txe_atten)])
    csvwriter.writerow([])

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
        capture = sh.expect("Power in region: .*\d\.")
        pwrtime, pwrfreq, regionpwr = re.search("RMS Power: (\-?\d+\.\d+).*RMS Power: (\-?\d+\.\d+).*region: (\-?\d+\.\d+)\.", capture).groups()

        ## Bookkeeping
        row = [float(freq), float(chanpwr), float(srxpower), float(pwrtime), float(pwrfreq), float(regionpwr)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
        os.sync()
