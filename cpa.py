#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import argparse
import logging as log

import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

import scass
    
argparser = argparse.ArgumentParser()

def parse_args(parser):
    """
    Parse command line arguments to the script
    """
    parser.add_argument("trace_set",type=argparse.FileType("rb"),
        help="File path to load trace set from")
    parser.add_argument("--key-bytes",type=int, default=16,
        help="Number of key bytes to guess")
    parser.add_argument("--message-bytes",type=int, default=16,
        help="Number of message bytes per block")
    parser.add_argument("--save-path", type=str, default=".",
        help="Where to save figures too.")
    parser.add_argument("--log", type=str, default="",
        help="Log file path for the attack")

    return parser

def main(
    args,
    analyser   = scass.cpa.CorrolationAnalysis,
    powermodel = scass.cpa.CPAModelHammingWeightD
    ):
    """
    Main function for the tool script
    """
    
    log.info("Loading traces: %s" % args.trace_set.name)
    ts_set_rd = scass.trace.TraceReaderSimple(args.trace_set)
    
    ts_set    = scass.trace.TraceSet()
    ts_set.loadFromTraceReader(ts_set_rd)

    cpa     = analyser(
        ts_set,
        keyBytes=args.key_bytes,
        messageBytes=args.message_bytes
    )

    log.info("Trace Length      : %d" % cpa.T)
    log.info("Trace Count       : %d" % cpa.D)
    #log.info("Aux Data Shape    : %s" % str(cpa.amat.shape))
    #log.info("Trace Data Shape  : %s" % str(cpa.tmat.shape))

    guesses = []


    for b in tqdm(range(0, args.key_bytes)):
        
        V       = cpa.computeV(msgbyte = b)
        H       = cpa.computeH(V)
        guess,R = cpa.computeR(H)

        guesses.append(guess)

        fig = plt.figure()
        plt.clf()

        plt.suptitle("Key guess: %s (%d)" % (hex(guess),guess))
        
        plt.subplot(211)
        plt.plot(R, linewidth=0.2)
        
        plt.subplot(212)
        plt.plot(R.transpose(), linewidth=0.2)

        fig.set_size_inches(20,10,forward=True)
        plt.savefig("%s/%d.png" % (args.save_path,b))
        
    
    log.info("Key Guess: %s" %([hex(g) for g in guesses]))
    log.info("--- Finish ---")
    

if(__name__ == "__main__"):
    args        = parse_args(argparser).parse_args()
    if(args.log != ""):
        log.basicConfig(filename=args.log,filemode="w",level=log.INFO)
    else:
        log.basicConfig(level=log.INFO)
    sys.exit(main(args))


