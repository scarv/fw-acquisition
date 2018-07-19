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
    
    parser.add_argument("--source", type=argparse.FileType("r"), 
        help="A script file to source and run")
    
    return parser.parse_args()


def main():
    """
    Main program loop.
    """
    args  = parse_args()
    shell = sassrig.SAFShell()

    if(args.port):
        shell.do_connect("%s %d"%(args.port, args.baud))

    if(args.source):
        # We need to feed the shell a file one line at a time.

        with args.source as fh:

            for line in fh.readlines():
                
                toprint = line.rstrip("\n")

                print(">> %s" % toprint)

                if(line[0] == "#"):
                    pass
                else:
                    try:
                        stop = shell.onecmd(line)

                        if(stop):
                            break

                    except Exception as e:
                        print("Exception Occured: %s" % str(e))
                        sys.exit(1)


    else:
        # Enter an interactive loop

        try:
            shell.cmdloop()
        except Exception as e:
            print("Exception Occured: %s" % str(e))
            sys.exit(1)

    sys.exit(0)

if(__name__ == "__main__"):
    main()
