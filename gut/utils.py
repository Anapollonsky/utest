import sys
import os

# http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
def recursive_dict_merge(a, b):
    """ Merges dictionaries a and b

    Performs an in-place merge of dictionaries and their nested lists.
    a gets priority over b in case of conflicts."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in b:
            if key in a:
                if (isinstance(a[key], dict) and isinstance(b[key], dict)) or (isinstance(a[key], list) and isinstance(b[key], list)):
                    recursive_dict_merge(a[key], b[key])
                else:
                    pass # if identical singles or different, a stays same
            else:
                a[key] = b[key]

    elif isinstance(a, list) and isinstance(b, list):
        for k in b:
            a.append(k)
    else:
        print("Merge error! " + str(a) + str(b))
        sys.exit()
    return a

# http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def getTerminalSize():
    """ Record the terminal size """
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])
