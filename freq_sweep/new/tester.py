from BCI_Interface import BCI
from Shell_Interface import Shell
from FTP_Interface import FTP
from time import sleep
import csv
import re

board = "135.112.98.31"
lofreq = 1800000 
hifreq = 2100001
step = 50000

bci = BCI(board, "lucent", "password")
sh = Shell()
ftp = FTP(board, "lucent", "password")

print("Connections established...")
bci.tx_set_atten(8, 255)
print("Attenuation Set...")
bci.tx_set_rf_switches(0, 0)
print("RF Switches Set...")

with open('data.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    for freq in range(lofreq, hifreq, step):
        filename = "srx_capture"
        bci.tx_set_lo(0, freq)
        srxpower = bci.get_srx_power(0)

        ## Capture
        bci.srx_capture("/tmp/" + filename)
        bci.srx_capture("/tmp/" + filename)
        bci.srx_capture("/tmp/" + filename)
        sh.sendline("rm -f " + filename)
        sleep(.2)
        ftp.get("/tmp/" + filename)

        ## Octave
        sh.sendline("./das_capture_power.m %s 307.2 0 10" % filename)
        capture = sh.expect("Power in region: .* dBFs\.")
        totalpwr, regionpwr = re.search("RMS Power: (\-\d+\.\d+).*region: (\-\d+\.\d+)", capture).groups()

        ## Bookkeeping
        row = [float(freq), float(srxpower), float(totalpwr), float(regionpwr)]
        print("Appending row " + str(row))
        csvwriter.writerow(row)
        # sleep(30)
