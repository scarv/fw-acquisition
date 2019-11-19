#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import argparse
import logging as log

import gzip
import numpy as np
import matplotlib.pyplot as plt

scass_path = os.path.expandvars(
    os.path.join(os.path.dirname(__file__),"../")
)
sys.path.append(scass_path)

import scass

def parse_args():
    """
    Parse command line arguments to the script
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--graph-ttest",type=str, default = None,
        help="If set, write the T statistic trace graph to this file.")

    parser.add_argument("--critical-value",type=float,default=4.5,
        help="Critical value for TTest threshold")

    parser.add_argument("--second-order",action="store_true",default=False,
        help="Do a second order TTest.")

    parser.add_argument("--ttrace-dump",type=argparse.FileType("wb"),
        help="Dump the resulting ttrace to this file for later use.")
    
    parser.add_argument("trs_fixed",type=str,
        help="File path of .npy array indicating if traces are fixed or random.")

    parser.add_argument("trs_trace",type=str,
        help="File path of .npy file containing the traces")
    

    return parser.parse_args()

def main():
    """
    Main function for the tool script
    """
    args        = parse_args()

    log.info("Loading traces...")
    
    gzfh_fixed  = gzip.GzipFile(args.trs_fixed,"r")
    gzfh_traces = gzip.GzipFile(args.trs_trace,"r")

    fbits       = np.load(gzfh_fixed)
    traces      = np.load(gzfh_traces)

    fixed_idx   = np.nonzero(fbits >= 1)
    rand_idx    = np.nonzero(fbits <  1)

    ts_fixed    = traces[fixed_idx]
    ts_random   = traces[ rand_idx]

    log.info("Running TTest...")
    ttest       = scass.ttest.TTest (
        ts_fixed,
        ts_random,
        second_order = args.second_order
    )

    if(args.ttrace_dump):
        log.info("Writing T Trace to: %s" % args.ttrace_dump.name)
        np.save(args.ttrace_dump, ttest.ttrace)

    if(args.graph_ttest):
        log.info("Writing T Statistic Graph: %s" % args.graph_ttest)
        plt.clf()
        fig = plt.gcf()
        plt.tight_layout
        plt.title("TTest Results")
        plt.xlabel("Sample")
        plt.ylabel("Leakage")
        plt.plot(ttest.ttrace, linewidth=0.1)

        plt.plot(
            [args.critical_value]*ttest.ttrace.size,
            linewidth=0.25,color="red"
        )
        plt.plot(
            [-args.critical_value]*ttest.ttrace.size,
            linewidth=0.25,color="red"
        )

        fig.set_size_inches(10,5,forward=True)
        plt.savefig(args.graph_ttest,bbox_inches="tight", pad_inches=0)


if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())


