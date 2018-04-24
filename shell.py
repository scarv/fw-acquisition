#!/usr/bin/python3


import os
import re
import sys
import shlex
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
    
    parser.add_argument("port", type=str,
        help="Target serial port to use")
    parser.add_argument("baud", type=int,
        help="Baud rate for the serial port.")
    
    return parser.parse_args()


def main():
    """
    Main program loop.
    """
    args = parse_args()

    if(args.v or args.V):
        if(args.V):
            log.basicConfig(level=log.DEBUG)
        else:
            log.basicConfig(level=log.INFO)
    else:
        log.basicConfig(level=log.WARN)

    
    comms = sassrig.SassComms(
        serialPort = args.port,
        serialBaud = args.baud
    )

    exit = False

    while(not exit):

        line = input("SASS $> ")

        lexed = shlex.split(line)

        if(len(lexed) <=  0):
            continue

        cmd = lexed[0]
        
        if(cmd == "exit"):
            exit = True
        elif(cmd == "helloworld"):
            value = comms.doHelloWorld()
            print(value)
        elif(cmd == "get_cfg"):
            field = bytes([int(lexed[1])])
            value = comms.doGetCfg(field)
            print(value)
        elif(cmd == "set_cfg"):
            field = bytes([int(lexed[1])])
            value = bytes(lexed[2],encoding="ascii")
            value = comms.doSetCfg(field, value)
            print(value)

    comms.ClosePort()
    sys.exit(0)


if(__name__ == "__main__"):
    main()
