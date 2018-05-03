#!/usr/bin/python3


import os
import re
import sys
import shlex
import argparse
import logging as log

import pyaes
import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

import sassrig


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("port", type=str,
        help="Target serial port to use")
    parser.add_argument("baud", type=int,
        help="Baud rate for the serial port.")
    
    parser.add_argument("-v", action="store_true", 
        help="Turn on verbose logging.")
    parser.add_argument("-V", action="store_true", 
        help="Turn on very verbose logging.")
    
    parser.add_argument("--num-traces", type=int, default=10000,
        help="How many traces to capture for each set?")

    parser.add_argument("--batch", action="store_true",
        help="Don't show graphs.")

    parser.add_argument("--dump-traces", action="store_true",
        help="Write the captured traces to a file.")

    parser.add_argument("--constant-message", action="store_true",
        help="If set, the plaintext will be kept constant during the runs.")
    
    return parser.parse_args()


def capture_traces(num_traces, scope, comms, message, key, args):
    """
    Capture the supplied number of traces and put them in storage.
    """
    storage         = sassrig.SassStorage()
    
    pb = tqdm(range(0,num_traces))
    pb.set_description("Capturing Trace Set")
    
    edec = sassrig.SassEncryption()
    comms.doSetKey(key)

    for i in pb:
        
        if(not args.constant_message):
            message         = edec.GenerateMessage()
            comms.doSetMsg(message)

        scope.StartCapture()
        comms.doEncrypt()
        scope.WaitForReady()
        
        data  = scope.GetData(scope.sample_channel)
        trace = sassrig.SassTrace(data, key=key,message=message)
        storage.AddTrace(trace)

    return storage

def shuffler_enable(comms):
    log.info("Enable shuffler")
    comms.doSetCfg(bytes([0]),bytes([1]))

def shuffler_disable(comms):
    log.info("Disable shuffler")
    comms.doSetCfg(bytes([0]),bytes([0]))


def check_correctness(comms, edec):
    """
    Make sure we get the right answer when encrypting and decrypting.
    """
    key                 = edec.GenerateKeyBits()
    plaintext           = edec.GenerateMessage()
    aes                 = pyaes.AESModeOfOperationECB(key)
    oracle_ciphertext   = aes.encrypt(plaintext)

    comms.doSetKey(key)
    comms.doSetMsg(plaintext)
    comms.doEncrypt()
    test_ciphertext     = comms.doGetCipher()

    if(oracle_ciphertext != test_ciphertext):
        log.error("Encypt error: Oracle = %s, Test = %s" % (
            oracle_ciphertext.hex(), test_ciphertext.hex()))
        return False
    else:
        return True


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

    edec = sassrig.SassEncryption()
    
    message         = edec.GenerateMessage()
    key             = edec.GenerateKeyBits()
    num_traces      = args.num_traces

    log.info("Traces : %d" % num_traces)
    log.info("Message: %s" % message)
    log.info("Key    : %s" % key    )

    log.info("Opening scope connection...")
    scope           = sassrig.SassScope()
    scope.OpenScope()
    scope.ConfigureScope()

    # First trace set with the shuffler off
    log.info("Capturing non-shuffler traces...")
    shuffler_disable(comms)
    check_correctness(comms,edec)
    traces_control  = capture_traces(num_traces,scope,comms, message,key,args)

    # Next trace set with the shuffler on
    log.info("Capturing shuffled traces...")
    shuffler_enable(comms)
    check_correctness(comms,edec)
    traces_shuffler = capture_traces(num_traces,scope,comms, message,key,args)
    shuffler_disable(comms)

    log.info("Trace gathering complete.")

    if(args.dump_traces):
        log.info("Writing captured traces to disk")
        control_fname = "traces-control-%s.trs"%(key.hex())
        shuffle_fname = "traces-shuffle-%s.trs"%(key.hex())
        traces_control.DumpTRS(control_fname)
        traces_shuffler.DumpTRS(shuffle_fname)

    # plot the two trace sets side by side
    fig = plt.figure(1)
    if(args.constant_message):   
        fig.suptitle("Shuffler Trace Comparison (changing key/message)")
    else:
        fig.suptitle("Shuffler Trace Comparison (constant key/message)")

    plt.tight_layout(0)

    if(not args.batch):

        # Control traces
        ctrl_plot = plt.subplot(1,1,1)
        ctrl_plot.set_title("Control 0 - shuffler disabled")
        control_traces = np.array([t.data for t in traces_control.traces])
        control_traces = np.mean(control_traces,axis=0)
        plt.plot(control_traces, linewidth=0.25)
        

        # Shuffler traces
        shf_plot = plt.subplot(2,1,2)
        shf_plot.set_title("Test - shuffler enabled")
        shuffle_traces = np.array([t.data for t in traces_shuffler.traces])
        shuffle_traces = np.mean(shuffle_traces,axis=0)
        plt.plot(shuffle_traces, linewidth=0.25)
        
        # Difference between the two.
        shf_plot = plt.subplot(3,1,3)
        shf_plot.set_title("Difference - control 0 / shuffled")
        difference = control_traces - shuffle_traces
        plt.plot(difference, linewidth=0.25)

        plt.show()

    # Cleanup and exit
    comms.ClosePort()
    sys.exit(0)


if(__name__ == "__main__"):
    main()
