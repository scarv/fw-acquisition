#!/usr/bin/python3

"""
A script for creating simple plots from trace sets.
"""

import os
import sys
import secrets
import argparse
import logging as log

import numpy as np
import matplotlib.pyplot as plt

scass_path = os.path.expandvars(
    os.path.join(os.path.dirname(__file__),"../")
)
sys.path.append(scass_path)

import scass

def build_arg_parser():
    """
    Parse command line arguments to the script.
    """
    
    parser = argparse.ArgumentParser()

    parser.add_argument("--avg-trace",action="store_true",
        help="Add the average trace to the plot")

    parser.add_argument("--stddev",action="store_true",
        help="Add standard deviation to the plot")

    parser.add_argument("--minmax",action="store_true",
        help="Add Minimum / maximum values of each trace sample to the plot")

    parser.add_argument("--range",action="store_true",
        help="Add range of each trace sample to the plot")

    parser.add_argument("--transpose-over-time",action="store_true",
        help="Plot the raw-trace set values over time, but transpose them")

    parser.add_argument("traceset",type=argparse.FileType("rb"),
        nargs="+",
        help="The set of traces to analyse")

    parser.add_argument("graph",type=str,
        help="Filepath of the graph to create")
    
    return parser

def main(argparser):
    """
    Script main function
    """
    args = argparser.parse_args()

    log.info("Loading traceset...")
        
    fig = plt.figure()
    fig.set_size_inches(9.5,5,forward=True)

    for tset in args.traceset:

        reader = scass.trace.TraceReaderSimple(tset)
        tset   = scass.trace.TraceSet()
        tset.loadFromTraceReader(reader)

        if(args.avg_trace):
            plt.plot(tset.averageTrace(), linewidth=0.1)

        if(args.stddev):
            plt.plot(tset.standardDeviation(), linewidth=0.1)
        
        if(args.minmax):
            plt.plot(tset.minTrace(), linewidth=0.1)
            plt.plot(tset.maxTrace(), linewidth=0.1)
        
        if(args.range):
            plt.plot(tset.maxTrace() - tset.minTrace(), linewidth=0.1)

        if(args.transpose_over_time):
            plt.plot(tset.tracesAs2dArray().transpose(),linewidth=0.1)

    plt.tight_layout()
        
    fig.savefig(args.graph)



if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    main(build_arg_parser())
