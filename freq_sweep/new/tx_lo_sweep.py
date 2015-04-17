from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from N9020A_Interface import N9020A
from conman import Conman
from time import sleep
import datetime
from math import log
import csv
import re
import os
import argparse
import sys

VERSION = 4

## Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("band", help="hb/lb, highband or lowband")
parser.add_argument("tx", help="transmitter 1/2")
parser.add_argument("board", help="board address")
parser.add_argument("mxa", help="mxa address, expected model N9020A")
parser.add_argument("-s", "--step", help="step size, in hz", default = 1e6, type=float)
parser.add_argument("-b", "--bandwidth", help="bandwidth, in hz", default = 5e6, type=float)
parser.add_argument("-w", "--waveform", help="waveform filename" , default = "LTE_5MHz_1Carrier.bin")
parser.add_argument("-o", "--output", help="output filename" , default = None)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))

args = parser.parse_args() # Parse arguments

# Constants
conman = Conman("loss_profiles.yml", "band_info.yml") # Manages connections and other global state
band_info = dict(conman.storage["band_info"][args.band])

## Variable Configuration
board = args.board
mxaaddr = args.mxa
lofreq = band_info["lofreq"] 
hifreq = band_info["hifreq"]
step = args.step 
bandwidth = args.bandwidth 
waveform = args.waveform
timestamp =  datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_filename = args.output or "tx_lo_sweep_%s_%s_%s_%s.csv" % (args.band, args.tx, args.board, timestamp)
srx_atten = band_info["srx_atten"]
txi_atten = band_info["txi_atten"]
txe_atten = band_info["txe_atten"]

## Check that cable compensation entry exists
if not mxaaddr in conman.storage["loss_profiles_parsed"]:
    print("Cannot find loss profile, exiting.")
    sys.exit()

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxa = N9020A(mxaaddr) 
print("Connections established...")

# Capture filename
pid = os.getpid()
filename = "srx_capture" + str(pid)

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
mxa.do_reset()
mxa.set_continuous_sweep(True)
mxa.set_mech_atten(20)
mxa.set_ref_level(10)
mxa.set_detector("AVER")
mxa.set_mode("CHP")
mxa.sendline("CHP:FREQ:SYNT:AUTO ON")
mxa.sendline("CHP:IF:GAIN:AUTO ON")
mxa.set_averaging_count(500)
mxa.set_integration_bandwidth(5e6)
mxa.set_resolution_bandwidth(3e4)
mxa.sendline("CHP:BAND:VIDEO:AUTO OFF")
mxa.set_video_bandwidth(3e5)
mxa.set_span(7.5e6) 
mxa.set_auto_align(False)
mxa.do_manual_alignment()
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
                        "Freq-Domain Power", "Bandwidth Power", "Cable Loss"])

    # Data
    for freq in range(int(lofreq), int(hifreq) + 1, int(step)):
        bci.set_lo(0, freq)
        mxa.set_freq(freq)
        loss = "%0.2f" % conman.get_loss_at_freqs(freq, mxaaddr)[0]
        mxa.set_external_gain(loss)
        sleep(1)
        srxpower = bci.get_srx_power(0)
        chanpwr, _ = mxa.get_chanpwr_psd()

        ## Capture
        sh.sendline("rm -f " + filename)
        for k in range(3): # Prevent repetition of data
            bci.do_srx_capture("/tmp/" + filename)
        ftp.get("/tmp/" + filename)
        
        ## Octave
        pwrtime, pwrfreq, regionpwr = Conman.das_capture_power(sh, filename, 0, int(bandwidth/1e6)) 

        ## Bookkeeping
        row = [float(freq), float(chanpwr), float(srxpower), float(pwrtime), float(pwrfreq), float(regionpwr), float(loss)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
