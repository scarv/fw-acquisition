#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import argparse
import logging as log

import matplotlib.pyplot as plt

import scass

def parse_args():
    """
    Parse command line arguments to the script
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("trace_set",type=argparse.FileType("rb"),
        help="File path to load trace set from")

    return parser.parse_args()

def main():
    """
    Main function for the tool script
    """
    args        = parse_args()
    
    log.info("Loading traces...")
    ts_set_rd = scass.trace.TraceReaderSimple(args.trace_set)
    
    ts_set    = scass.trace.TraceSet()
    ts_set.loadFromTraceReader(ts_set_rd)

    model   = scass.cpa.CPAModel()
    cpa     = scass.cpa.CorrolationAnalysis(ts_set)


    log.info("Trace Length      : %d" % cpa.tlen)
    log.info("Trace Count       : %d" % cpa.tnum)
    log.info("Aux Data Shape    : %s" % str(cpa.amat.shape))
    log.info("Trace Data Shape  : %s" % str(cpa.tmat.shape))

    log.info("Computing H...")
    H       = cpa.computeH(model)

    log.info("Computing Corrolation...")
    corr    = cpa.getCorrolation(H)

    fig     = plt.figure()
    plt.plot(corr,linewidth=0.2)
    plt.show()
    
    log.info("--- Finish ---")
    

if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())


