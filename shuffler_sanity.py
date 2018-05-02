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
    
    parser.add_argument("-v", action="store_true", 
        help="Turn on verbose logging.")
    parser.add_argument("-V", action="store_true", 
        help="Turn on very verbose logging.")
    
    parser.add_argument("port", type=str,
        help="Target serial port to use")
    parser.add_argument("baud", type=int,
        help="Baud rate for the serial port.")
    
    return parser.parse_args()


def capture_traces(num_traces, scope, comms, key, args,msg,edec):
    """
    Capture the supplied number of traces and put them in storage.
    """
    storage         = sassrig.SassStorage()
    
    pb = tqdm(range(0,num_traces))
    pb.set_description("Capturing Trace Set: %s, %s, %s" % msg)
    
    comms.doSetKey(key)

    for i in pb:
        
        message         = edec.GenerateMessage()
        comms.doSetMsg(message)

        scope.StartCapture()
        comms.doEncrypt()
        scope.WaitForReady()
        
        data  = scope.GetData(scope.sample_channel)
        trace = sassrig.SassTrace(data, key=key,message=message)
        storage.AddTrace(trace)

    return storage


def set_shuffler_enable(comms, enable):
    log.info("Enable shuffler: %s" % enable)
    if(enable):
        comms.doSetCfg(bytes([0]),bytes([1]))
    else:
        comms.doSetCfg(bytes([0]),bytes([0]))


def set_shuffler_scheme(comms,scheme):
    if (scheme == "bayrak" ):
        comms.doSetCfg(bytes([2]),bytes([1]))
    elif (scheme == "new"):
        comms.doSetCfg(bytes([2]),bytes([2]))
    else:
        log.error("Unknown scheme: %s" % scheme)
        sys.exit(1)
    log.info("Set Scheme: %s" % scheme)

def set_aes_implementation(comms,impl):
    if (impl == "unrolled" ):
        comms.doSetCfg(bytes([3]),bytes([0]))
    elif (impl== "looped"):
        comms.doSetCfg(bytes([3]),bytes([1]))
    elif (impl== "reference"):
        comms.doSetCfg(bytes([3]),bytes([2]))
    else:
        log.error("Unknown aes implementation: %s" % impl)
        sys.exit(1)
    log.info("Set AES implementation: %s" % impl)


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



def run_sanity(args,comms,edec,scope):
    """
    Run a bunch of sanity tests
    """
    shuffler_scheme = ["bayrak","new"]
    aes_implementation = ["reference","looped","unrolled"]

    key = edec.GenerateKeyBits()
    num_traces = 10

    plt.ion()

    idx = 0

    for scheme in shuffler_scheme:
        for aes in aes_implementation:
            set_aes_implementation(comms,aes)
            set_shuffler_scheme(comms,scheme)

            set_shuffler_enable(comms,False)

            print("Scheme = %s, AES = %s, shuffle enable=%s"%(
                scheme,aes,False))
            
            if(not check_correctness(comms,edec)):
                sys.exit(1)

            dis_traceid = (aes,False,scheme)
            dis_traces = capture_traces(num_traces,scope,
                                    comms,key,args,dis_traceid,edec)
            
            set_shuffler_enable(comms,True)
            
            print("Scheme = %s, AES = %s, shuffle enable=%s"%(
                scheme,aes,True))
            
            if(not check_correctness(comms,edec)):
                sys.exit(1)

            en_traceid = (aes,True,scheme)
            en_traces = capture_traces(num_traces,scope,
                                    comms,key,args,en_traceid,edec)
            
            points_en = np.array([t.data for t in en_traces.traces])
            points_en = np.mean(points_en,axis=0)

            points_dis= np.array([t.data for t in dis_traces.traces])
            points_dis= np.mean(points_dis,axis=0)

            fig = plt.figure(1)

            limits = [min(points_en.min(),points_dis.min()),
                      max(points_en.max(),points_dis.max())]

            
            plt.subplot(6,3,idx*3+1)
            plt.plot(points_dis,linewidth=0.25)
            plt.title("Trace capture: %s, %s, %s" % dis_traceid)
            plt.ylim(limits)
            
            plt.subplot(6,3,idx*3+2)
            plt.plot(points_en,linewidth=0.25)
            plt.title("Trace capture: %s, %s, %s" % en_traceid)
            plt.ylim(limits)
            
            plt.subplot(6,3,idx*3+3)
            plt.plot(points_en-points_dis,linewidth=0.25)
            plt.title("Difference")
            plt.ylim(limits)

            plt.draw()
            plt.pause(0.001)
            plt.show()
            plt.tight_layout(0);
            idx += 1

    plt.ioff()
    plt.show()


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

    log.info("Opening scope connection...")
    scope               = sassrig.SassScope()
    scope.sample_count  = 20000
    scope.OpenScope()
    scope.ConfigureScope()
    
    run_sanity(args,comms,edec,scope)

    # Cleanup and exit
    comms.ClosePort()
    sys.exit(0)


if(__name__ == "__main__"):
    main()
