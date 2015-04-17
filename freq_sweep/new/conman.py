import yaml
import sys
import numpy as np
import re

class Conman(object):

    units = {"hz": 1,
             "khz": 1e3,
             "mhz": 1e6,
             "ghz": 1e9}
    
    def __init__(self, *sources):
        """Initialize, adding all sources as passed in a list"""
        self.storage = {}
        for source in sources:
            self.add_source(source)

    def ferror(self, message):
        """Fatal error message"""
        print("ERROR: %s" % message)
        sys.exit()

    def warning(self, message):
        print("WARNING: %s" % message)
        
    def add_source(self, source):
        """Add contents of source to conman database"""
        try:
            infile = open(source, 'r')
            contents = yaml.load(infile.read()) 
        except IOError:
            self.ferror("Failed to load source %s." % str(source))
        except:
            self.ferror("Failed to parse YAML source")
        self.storage.update(contents)
        self._parse_loss_profiles()
        infile.close()

    def write_to_yaml(self, filename, path = []):
        """Export a data structure in storage, taking an optional path
        argument to specify which data structure. By default, the entire
        storage is exported."""
        outfile = open(filename, 'w')
        yaml.dump(self.storage, outfile)
        outfile.close()

    def _parse_loss_profiles(self):
        self.storage["loss_profiles_parsed"] = {}
        for address in self.storage["loss_profiles"]:
            address_dict = self.storage["loss_profiles"][address]
            freqlist = []
            for freqstr in address_dict:
                match = re.search("(\-?\d*\.?\d*)([a-zA-z]*)", freqstr)
                if not match:
                    self.warning("Unable to parse loss profile entry %s" % freqstr)
                    continue
                numhz = float(match.groups()[0]) * Conman.units[match.groups()[1].lower()]
                freqlist.append([numhz, address_dict[freqstr]])
            freqlist = sorted(freqlist, key=lambda x: x[0])
            self.storage["loss_profiles_parsed"][address] = np.transpose(np.array(freqlist, float)) 

    def get_loss_at_freqs(self, freqs, address):
        if address in self.storage["loss_profiles_parsed"]:
            freqs = [freqs] if not isinstance(freqs, list) else freqs
            data = self.storage["loss_profiles_parsed"][address]
            return list(np.interp(freqs, data[0, :], data[1, :]))
        else:
            return None
        
    @staticmethod
    def das_capture_power(sh, filename, offset, bandwidth):
        """ Calls the das_capture_power script. Args: Shell instance, filename, offset and bandwidth"""
        sh.sendline("./das_capture_power.m %s 307.2 %d %d" % (filename, int(offset/1e6), int(bandwidth/1e6)))
        capture = sh.expect("Power in region: .*\d\.\d{2}")
        return re.search("RMS Power: (\-?\d+\.?\d*).*RMS Power: (\-?\d+\.?\d*).*region: (\-?\d+\.?\d*)", capture).groups()

