#!/usr/bin/python3


import os
import re
import sys
import shlex
import argparse
import logging as log

import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

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
    
    parser.add_argument("--num-traces", type=int, default=10000,
        help="How many traces to capture for each set?")

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
    traces_control_0  = capture_traces(num_traces,scope,comms, message,key,args)
    #traces_control_1  = capture_traces(num_traces,scope,comms, message,key,args)

    # Next trace set with the shuffler on
    log.info("Capturing shuffled traces...")
    shuffler_enable(comms)
    traces_shuffler = capture_traces(num_traces,scope,comms, message,key,args)
    shuffler_disable(comms)

    log.info("Trace gathering complete.")

    if(args.dump_traces):
        log.info("Writing captured traces to disk")
        control_fname = "traces-control-[key].trs".replace("[key]",key.hex())
        shuffle_fname = "traces-shuffle-[key].trs".replace("[key]",key.hex())
        traces_control_0.DumpTRS(control_fname)
        traces_shuffler.DumpTRS(shuffle_fname)

    # plot the two trace sets side by side
    fig = plt.figure(1)
    if(args.constant_message):   
        fig.suptitle("Shuffler Trace Comparison (changing key/message)")
    else:
        fig.suptitle("Shuffler Trace Comparison (constant key/message)")

    plt.tight_layout(0)

    # Control traces
    ctrl_plot = plt.subplot(3,1,1)
    ctrl_plot.set_title("Control 0 - shuffler disabled")
    control_traces_0 = np.array([t.data for t in traces_control_0.traces])
    control_traces_0 = np.mean(control_traces_0,axis=0)
    plt.plot(control_traces_0, linewidth=0.25)
    
    #ctrl_plot = plt.subplot(3,2,2)
    #ctrl_plot.set_title("Control 1 - shuffler disabled")
    #control_traces_1 = np.array([t.data for t in traces_control_1.traces])
    #control_traces_1 = np.mean(control_traces_1,axis=0)
    #plt.plot(control_traces_1, linewidth=0.25)

    # Shuffler traces
    shf_plot = plt.subplot(3,1,2)
    shf_plot.set_title("Test - shuffler enabled")
    shuffle_traces = np.array([t.data for t in traces_shuffler.traces])
    shuffle_traces = np.mean(shuffle_traces,axis=0)
    plt.plot(shuffle_traces, linewidth=0.25)
    
    shf_plot = plt.subplot(3,1,3)
    shf_plot.set_title("Difference - control 0 / shuffled")
    difference = control_traces_0 - shuffle_traces
    plt.plot(difference, linewidth=0.25)
    plt.ylim([shuffle_traces.min(),shuffle_traces.max()])
    
    #shf_plot = plt.subplot(3,2,6)
    #shf_plot.set_title("Difference - control 0 / control 1")
    #difference = control_traces_1 - control_traces_0
    #plt.plot(difference, linewidth=0.25)
    #plt.ylim([shuffle_traces.min(),shuffle_traces.max()])

    plt.show()

    # Cleanup and exit
    comms.ClosePort()
    sys.exit(0)


if(__name__ == "__main__"):
    main()
