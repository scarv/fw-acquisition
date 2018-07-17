#!/usr/bin/python3


import os
import re
import sys
import argparse
import logging as log

import sassrig


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-v", action="store_true", 
        help="Turn on verbose logging.")
    parser.add_argument("-V", action="store_true", 
        help="Turn on very verbose logging.")
    
    parser.add_argument("--port", type=str,
        help="Target serial port to use")
    parser.add_argument("--baud", type=int, default=115200,
        help="Baud rate for the serial port.")
    
    return parser.parse_args()


def main():
    """
    Main program loop.
    """
    args  = parse_args()
    shell = sassrig.SAFShell()

    if(args.port):
        shell.do_connect("%s %d"%(args.port, args.baud))

    shell.cmdloop()

if(__name__ == "__main__"):
    main()
