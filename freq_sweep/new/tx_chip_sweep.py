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
parser.add_argument("-w", "--waveform", help="waveform filename" , default = "Chipmix_APT_duc_2lte_mode7_evm.bin")
args = parser.parse_args() # Parse arguments

## Variable Configuration
bands = {"lb": [717e6, 894e6],
         "hb": [1805e6, 2.2e9]}
center_freqs = {a:(bands[a][0] + bands[a][1])/2 for a in bands}
ranges = {a:[center_freqs[a] - 30e6, center_freqs[a] + 30e6] for a in center_freqs}


board = args.board
mxaaddr = args.mxa
lofreq = ranges[args.band][0] # Goes by 'step' from lofreq (inclusive) to highfreq (inclusive)
hifreq = ranges[args.band][1]
step = args.step 
bandwidth = args.bandwidth 
waveform = args.waveform 
csv_filename = "tx_chip_sweep_%s_%s_%s_%s.csv" % (args.band, args.tx, args.board, args.mxa)

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

# bci.set_tone_gain(0)

# Transmitter
if args.tx == "1":
    bci.set_tx_rf_switches(0, 3)
elif args.tx == "2":
    bci.set_tx_rf_switches(0, 0)

# Lock
center_freq = (hifreq + lofreq) / 2
bci.set_lo(0, center_freq)
assert bci.ensure_reference_pll_lock("EXT", 1)
print("Board configured...")

# MXA Setup
mxa.do_jeff_mxa_setup()
mxa.set_freq(center_freq)
print("MXA configured...")

# Waveform
ftp.put(waveform, "/tmp/")
print("Waveform transferred...")

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
        offset = int(freq - center_freq) 
        bci.do_chiprate_play_waveform("/tmp/" + waveform, offset, 0)
        mxa.set_freq(freq)
        sleep(2)
        srxpower = bci.get_srx_power(0)
        chanpwr, _ = mxa.get_chanpwr_psd()

        ## Capture
        for k in range(3): # Prevent repetition of data
            bci.do_srx_capture("/tmp/" + filename)
        sh.sendline("rm -f " + filename)
        ftp.get("/tmp/" + filename)
        
        ## Octave
        sh.sendline("./das_capture_power.m %s 307.2 %d %d" % (filename, (offset/1e6), int(bandwidth/1e6)))
        capture = sh.expect("Power in region: .*\d\.")
        pwrtime, pwrfreq, regionpwr = re.search("RMS Power: (\-?\d+\.\d+).*RMS Power: (\-?\d+\.\d+).*region: (\-?\d+\.\d+)\.", capture).groups()

        ## Bookkeeping
        row = [float(freq), float(chanpwr), float(srxpower), float(pwrtime), float(pwrfreq), float(regionpwr)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
