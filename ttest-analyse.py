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

    parser.add_argument("--graph-ttest",type=str, default = None,
        help="If set, write the T statistic trace graph to this file.")
    
    parser.add_argument("trs_fixed",type=argparse.FileType("rb"),
        help="File path to store fixed data trace set")

    parser.add_argument("trs_random",type=argparse.FileType("rb"),
        help="File path to store fixed data trace set")
    

    return parser.parse_args()

def main():
    """
    Main function for the tool script
    """
    args        = parse_args()
    
    log.info("Loading fixed traces...")
    ts_fixed_rd = scass.trace.TraceReaderSimple(args.trs_fixed )

    log.info("Loading random traces...")
    ts_random_rd= scass.trace.TraceReaderSimple(args.trs_random)
    
    ts_fixed    = scass.trace.TraceSet()
    ts_fixed.loadFromTraceReader(ts_fixed_rd)
    log.info("Fixed data type  : %s" % str(ts_fixed_rd.dtype))

    ts_random   = scass.trace.TraceSet()
    ts_random.loadFromTraceReader(ts_random_rd)
    log.info("Random data type : %s" % str(ts_random_rd.dtype))

    log.info("Fixed Len     : %d" % ts_fixed.trace_length)
    log.info("Random Len    : %d" % ts_random.trace_length)
    log.info("Fixed traces  : %d" % ts_fixed.num_traces)
    log.info("Random traces : %d" % ts_random.num_traces)
    log.info("Fixed traces  : %d" % ts_fixed_rd.traces_read)
    log.info("Random traces : %d" % ts_random_rd.traces_read)

    log.info("Running TTest...")
    ttest       = scass.ttest.TTest(ts_fixed, ts_random)

    if(args.graph_ttest):
        log.info("Writing T Statistic Graph: %s" % args.graph_ttest)
        plt.clf()
        plt.plot(ttest.ttrace)
        plt.savefig(args.graph_ttest)
    

if(__name__ == "__main__"):
    log.basicConfig(level=log.DEBUG)
    sys.exit(main())


