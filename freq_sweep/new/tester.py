from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from N9020A_Interface import N9020A
from time import sleep
import csv
import re

## Configuration
board = "135.112.98.31"
lofreq = 1800000 
hifreq = 2100001
step = 50000
bandwidth = 5000

## Connections
bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")
mxa = N9020A("135.112.98.230") 
print("Connections established...")

## Setup
bci.set_tx_atten(8, 255)
bci.set_tx_rf_switches(0, 0)
bci.ensure_pll_lock(1)

print("Getting Channel power...")
print(mxa.get_channel_power(1800000, bandwidth, "KHz", "KHz"))


# with open('data.csv', 'w') as csvfile:
#     csvwriter = csv.writer(csvfile)
#     for freq in range(lofreq, hifreq, step):
#         filename = "srx_capture"
#         bci.set_tx_lo(0, freq)
#         srxpower = bci.get_srx_power(0)

#         ## Capture
#         for k in range(3): # Prevent repetition of data
#             bci.do_srx_capture("/tmp/" + filename)
#         sh.sendline("rm -f " + filename)
#         sleep(.2)
#         ftp.get("/tmp/" + filename)

#         ## Octave
#         sh.sendline("./das_capture_power.m %s 307.2 0 5" % filename)
#         capture = sh.expect("Power in region: .* dBFs\.")
#         totalpwr, regionpwr = re.search("S Power: (\-\d+\.\d+).*ion: (\-\d+\.\d+)", capture).groups()

#         ## Bookkeeping
#         row = [float(freq), float(srxpower), float(totalpwr), float(regionpwr)]
#         print("Appending row " + str(row))
#         csvwriter.writerow(row)
