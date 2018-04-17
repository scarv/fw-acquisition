#!/usr/bin/python3

"""
This is the front end script used to interract with the SASS-RIG.
"""

import os
import sys
import argparse

import sassrig

#
# List of possible commands we can give to the script
#
command_list = [
    "test"
]


def parse_args():
    """
    Responsible for parsing all arguments to the flow script.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--port", type=str, default="", 
        help="Which serial port used to communicate with the target.")
    parser.add_argument("--baud", type=int, default=19200, 
        help="Baud rate to communicate with the target at.")
    parser.add_argument("command", type=str, default="test", 
        choices=command_list, help="What to do?")

    return parser.parse_args()


def main():
    """
    Main function for the whole program
    """

    args = parse_args()

    comms = sassrig.SassComms(
        serialPort = args.port,
        serialBaud = args.baud
    )

    edec = sassrig.SassEncryption()

    if(args.command == "test"):
        
        rsp = comms.doHelloWorld()
        if(rsp):
            log.info("Successfully ran HelloWorld command with target")
        else:
            log.error("HelloWorld command failed")
            sys.exit(1)

    else:
        log.error("Unsupported command: %s" % args.command)
        sys.exit(1)

    sys.exit(0)



if(__name__ == "__main__"):
    main()
