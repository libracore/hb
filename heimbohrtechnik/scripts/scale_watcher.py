# Truck Scale Watcher
# Copyright (C) libracore AG, 2024-2026
#
# Make sure to run the watcher from the bench folder
#
# Command line arguments
#
#  $ python scale_watcher.py <scale> <interval>
#  $ python scale_watcher.py MudEx 10             watch MudEx Truck Scale, each 10 seconds
#

import time
import sys
import os
import subprocess

def main():
    # check mode
    truck_scale, interval = get_arguments()
    if not truck_scale:
        return                                  # quit
    interval = cint(interval)
    if interval < 1:                            # minimum interval: 1 second
        interval = 1
    
    if check_if_running():
        print("Watcher is already running. Please terminate the other watcher first.")
        return
        
    # reading loop: exit with CTRL-C
    params = """ "{'truck_scale': '""" + truck_scale + """'}" """
    while(True):
        # request trace
        os.system(f"""bench execute heimbohrtechnik.mudex.doctype.truck_scale.truck_scale.trace_weight --args '{truck_scale}' """)
        # wait
        time.sleep(interval)
        
    return
    
def cint(s):
    if not s:
        return 0
    else:
        return int(s)

def check_if_running():
    output = subprocess.check_output(["pgrep", "-f", "scale_watcher.py"]).decode()
    pids = [int(p) for p in output.split()]
    return any(pid != os.getpid() for pid in pids)


def get_arguments():
    n = len(sys.argv)
    if n < 3:
        print("Missing arguments. Please provide scale and interval")
        return None, None
    else:
        return sys.argv[1], sys.argv[2]



# *** START ***
main()
