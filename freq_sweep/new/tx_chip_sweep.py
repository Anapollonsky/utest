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

parser = argparse.ArgumentParser()
parser.add_argument("band", help="hb/lb, highband or lowband")
parser.add_argument("tx", help="transmitter 1/2")
parser.add_argument("board", help="board address")
parser.add_argument("mxa", help="mxa address, expected model N9020A")
parser.add_argument("-s", "--step", help="step size, in hz", default = 1e6, type=float)
parser.add_argument("-b", "--bandwidth", help="bandwidth of waveform, in hz", default = 5e6, type=float)
parser.add_argument("-w", "--waveform", help="waveform filename" , default = "awgn92MHz_122p88_minus18dBFs_noPL.bin")
parser.add_argument("-o", "--output", help="output filename" , default = None)
parser.add_argument("-c", "--center", help="lo center frequency", default = None, type=float) 
parser.add_argument("-r", "--range", help="max distance from center frequency", default = 3.75e7, type=float)
parser.add_argument("--version", help="print out version and exit",
                    action='version', version='%(prog)s ' + str(VERSION))

args = parser.parse_args() # Parse arguments

## Constants
conman = Conman("loss_profiles.yml", "band_info.yml") # Manages connections and other global state
band_info = dict(conman.storage["band_info"][args.band])
if not args.center:
    args.center = float((band_info["lofreq"] + band_info["hifreq"]) / 2)
band_info["cenfreq"] = args.center
band_info["lorang"] = band_info["cenfreq"] - args.range 
band_info["hirang"] = band_info["cenfreq"] + args.range 

## Variable Configuration
board = args.board
mxaaddr = args.mxa
lofreq = band_info["lorang"] 
hifreq = band_info["hirang"] 
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

## Setup
bci.set_output(False)
bci.set_output(True)

# Transmitter 
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

# Capture filename
pid = os.getpid()
filename = "srx_capture" + str(pid)

#Lock
bci.set_lo(0, band_info["cenfreq"])
assert bci.ensure_reference_pll_lock("EXT", 1)
print("Board configured...")

# Other BCI
bci.sendline("/pltf/txpath/txlointleakagecorrectInit")
bci.expect("SUCCESS")
bci.sendline("/pltf/txpath/txqecinit")
bci.expect("SUCCESS")
bci.fpga_write(0x0C, 0x0001)
sleep(4)
bci.fpga_write(0x0C, 0x0000)

# MXA Setup
mxa.do_reset()
mxa.set_continuous_sweep(True)
mxa.set_mech_atten(20)
mxa.set_ref_level(10)
mxa.set_detector("AVER")
mxa.set_integration_bandwidth(5e6)
mxa.set_resolution_bandwidth(3e4)
mxa.sendline("CHP:BAND:VIDEO:AUTO OFF")
mxa.set_auto_align(False)
mxa.do_manual_alignment()
mxa.echo(":INIT:SAN")
mxa.echo(":FREQ:CENTER %d Hz" % int(band_info["cenfreq"]))
mxa.echo(":FREQ:SPAN %d Hz" % 100e6)
mxa.echo(":TRACE1:TYPE AVERAGE")
mxa.echo(":AVER:COUNT 1000")
mxa.echo(":SENS:BAND:RES 1 MHz")
mxa.set_video_bandwidth(1e6)
mxa.set_freq(band_info["cenfreq"])
print("MXA configured...")

# Waveform
ftp.put(waveform, "/tmp/")
bci.do_tx_play_waveform("/tmp/" + waveform) 
print("Placed waveform at " + str(band_info["cenfreq"]/1e6) + " MHz...")

## Capture
sh.sendline("rm -f " + filename)
for k in range(3): # Prevent repetition of data
    bci.do_srx_capture("/tmp/" + filename)
ftp.get("/tmp/" + filename)
print("Capture performed...")

srxpower = bci.get_srx_power(0)
pwrtime, pwrfreq, _ = Conman.das_capture_power(sh, filename, 0, bandwidth)

print("Initial Setup Completed...")

print("Writing to " + csv_filename)
with open(csv_filename, 'w') as csvfile:
    ## CSV Header
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["tx_chip_sweep.py version: " + str(VERSION)])
    for member in [str(x) + ": " + str(y) for (x, y) in vars(args).items()]: # extract arguments, put in .csv file
        csvwriter.writerow([member])
    csvwriter.writerow(["readsrxpower 0: " + str(srxpower)])
    csvwriter.writerow(["Capture Freq-Domain Power: " + str(pwrfreq)])
    csvwriter.writerow(["Capture Time-Domain Power: " + str(pwrtime)])
    csvwriter.writerow(["SRX Attenuation: " + str(srx_atten)])
    csvwriter.writerow(["TX Internal Attenuation: " + str(txi_atten)])
    csvwriter.writerow(["TX External Attenuation: " + str(txe_atten)])
    csvwriter.writerow([])
    csvwriter.writerow(["Frequency", "Channel Power", "Bandwidth Power", "Cable Loss"])

    # Data
    for freq in range(int(lofreq), int(hifreq) + 1, int(step)):
        offset = int(freq - band_info["cenfreq"]) 

        # Find loss at frequency due to cables 
        loss = "%0.2f" % conman.get_loss_at_freqs(freq, mxaaddr)[0]
        mxa.set_external_gain(loss)
        chanpwr = mxa.get_value_at_freq(freq)
        
        ## Octave
        _1, _2, regionpwr = Conman.das_capture_power(sh, filename, offset, bandwidth)

        ## Bookkeeping
        row = [float(freq), float(chanpwr), float(regionpwr), float(loss)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)

        ## Update files
        csvfile.flush()
