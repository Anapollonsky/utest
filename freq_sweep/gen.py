import yaml
from copy import deepcopy

lofreq, hifreq = 700, 800
numsteps = 30

dshell = {"type": "command", "interface": "shell"}

dbci = {"type": "command",
        "interface":"bci",
        "address": "135.112.98.16",
        "username":"lucent",
        "password": "password"}

dbcio = dict(dbci)
dbcio["expect"] = "OK"

dbcis = dict(dbci)
dbcis["expect"] = "SUCCESS"

dbftp = {"type": "comand",
         "interface": "ftp",
         "username": "lucent",
         "password":"password",
         "address": "135.112.98.16"}
for freq in range(lofreq, hifreq, numsteps):
    capture_filename = "minis/mini" + str(freq) + ".yml" 
    bigstruct = {
        "do": [
            deepcopy(dbcio).update({"send": "/pltf/txPath/setLoFreq 0" + freq}),
            deepcopy(dbcis).update({"send": "/pltf/rxpath/fpgawrite 0x204 0x0"}),
            deepcopy(dbcis).update({"send": "/pltf/rxpath/fpgawrite 0xd 0x40"}),
            deepcopy(dbcis).update({"send": "/pltf/rxpath/fpgawrite 0x12 0x3"}),
            deepcopy(dbcis).update({"send": "/pltf/rxpath/fpgawrite 0x0 0xc077"}),
            deepcopy(dbcis).update({"send": "/pltf/rxpath/fpgawrite 0x12 0x0"}),
            deepcopy(dbci).update({"send": "/pltf/bsp/readfpgasram /tmp/" + capture_filename + " 12288000 2 0x01800000",
                                "wait_after": 5}),
            deepcopy(dbftp).update({"rcwd": "/tmp",
                                    "lcwd": "/home/aapollon/utest/freq_sweep",
                                    "get": capture_filename}),
            deepcopy(dshell).update({
                "send": "./das_capture_power.m " + capture_filename + " 307.2 0 5",
                "expect": "Power in region"})

        ]}

