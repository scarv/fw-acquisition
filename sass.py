#!/usr/bin/python3

"""
This is the front end script used to interract with the SASS-RIG.
"""

import os
import sys
import argparse
import logging as log

import matplotlib.pyplot as plt
from progress.bar import ShadyBar as progressbar

import sassrig

#
# List of possible commands we can give to the script
#
command_list = [
    "test-target",
    "test-scope",
    "test-flow"
]


def parse_args():
    """
    Responsible for parsing all arguments to the flow script.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", action="store_true", 
        help="Turn on verbose logging.")
    parser.add_argument("--port", type=str, default="", 
        help="Which serial port used to communicate with the target.")
    parser.add_argument("--baud", type=int, default=19200, 
        help="Baud rate to communicate with the target at.")
    parser.add_argument("command", type=str, default="test", 
        choices=command_list, help="What to do?")

    return parser.parse_args()


def test_target(comms, edec):
    """
    Runs a very simple set of tests to make sure the target and host are
    communicating properly.
    """
    rsp = comms.doHelloWorld()
    errcode   = 0
    if(rsp):
        log.info("Successfully ran HelloWorld command with target")
    else:
        log.error("HelloWorld command failed")
        errcode = 1

    t_message = edec.GenerateMessage()
    t_key     = edec.GenerateKeyBits()

    log.info("Set message to: " + t_message.hex())
    rsp = comms.doSetMsg(t_message)
    if(not rsp):
        log.error("Failed to set the message!")
        errcode = 1

    log.info("Set key to:     " + t_key.hex())
    rsp = comms.doSetKey(t_key)
    if(not rsp):
        log.error("Failed to set the key!")
        errcode = 1

    r_key     = comms.doGetKey()
    if(r_key == False):
        log.error("Could not read key back")
        errcode = 1
    elif(r_key != t_key):
        log.error("Sent " + t_key.hex() + " got " + r_key.hex())
        errcode = 1
    else:
        log.info("Read back key: " + r_key.hex())

    r_message = comms.doGetMsg()
    if(r_key == False):
        log.error("Could not read message back")
        errcode = 1
    elif(r_message != t_message):
        log.error("Sent " + t_message.hex()+ " got " + r_message.hex())
        errcode = 1
    else:
        log.info("Read back msg: " + r_message.hex())

    log.info("Trying Encryption...")
    rsp = comms.doEncrypt()
    if(not rsp):
        log.error("Encryption failed!")
        errcode = 1
    else:
        log.info("Encryption passed!")

    log.info("Trying Decryption...")
    rsp = comms.doDecrypt()
    if(not rsp):
        log.error("Decryption failed!")
        errcode = 1
    else:
        log.info("Decryption passed!")


    log.info("Test Finished")
    comms.ClosePort()
    sys.exit(errcode)


def test_scope():
    """
    A simple test function for connecting to the picoscope.
    """

    scope = sassrig.SassScope()

    log.info("Connecting to first available scope...")
    scope.OpenScope()
    
    scope.ConfigureScope()

    scope.CloseScope()

    sys.exit(0)


def test_flow(comms, edec):
    """
    Tests the control loop between the scope, host and target in order
    to capture a single trace.
    """

    log.info("Testing SASS-RIG Control loop")

    scope = sassrig.SassScope()

    log.info("Connecting to first available scope...")

    scope.OpenScope()
    scope.ConfigureScope()
    
    plt.figure(1)
    plt.ion()
    plt.show()

    pb = progressbar()
    pb.suffix = "%(percent).1f%% - %(eta)ds"
    pb.message= "Running"
    for i in pb.iter(range(0,50)):
        key = edec.GenerateKeyBits()
        msg = edec.GenerateMessage()

        log.info("Setting encryption parameters...")
        comms.doSetKey(key)
        comms.doSetMsg(msg)
        
        scope.StartCapture()
        comms.doEncrypt()

        scope.WaitForReady()
        
        plt.clf()
        plt.subplot(211)
        plt.plot(scope.GetData(scope.trigger_channel))

        plt.subplot(212)
        plt.plot(scope.GetData(scope.sample_channel))

        log.info("Number of Samples: %s", scope.no_of_samples)
        plt.draw()
        plt.pause(0.001)

    plt.ioff()
    plt.show()

    scope.CloseScope()
    comms.ClosePort()

    sys.exit(0)


def main():
    """
    Main function for the whole program
    """

    args = parse_args()

    if(args.v):
        
        log.basicConfig(level=log.INFO)




    if(args.command == "test-target"):
        
        comms = sassrig.SassComms(
            serialPort = args.port,
            serialBaud = args.baud
        )

        edec = sassrig.SassEncryption()

        test_target(comms,edec)   
    if(args.command == "test-flow"):
        
        comms = sassrig.SassComms(
            serialPort = args.port,
            serialBaud = args.baud
        )

        edec = sassrig.SassEncryption()

        test_flow(comms,edec)   

    elif(args.command == "test-scope"):
        
        test_scope()   

    else:
        log.error("Unsupported command: %s" % args.command)
        sys.exit(1)

    sys.exit(0)



if(__name__ == "__main__"):
    main()
