#!/usr/bin/python3

"""
A script for creating simple plots from trace sets.
"""

import os
import sys
import secrets
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

    parser.add_argument("traceset",type=str,
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
        
    fig = plt.figure()
    fig.set_size_inches(9.5,5,forward=True)

    for tset in args.traceset:

        gzfh   = gzip.GzipFile(tset,"r")
        traces = np.load(gzfh)

        if(args.avg_trace):
            plt.plot(np.mean(traces,axis=0), linewidth=0.1)

        if(args.stddev):
            plt.plot(np.std(traces,axis=0), linewidth=0.1)
        
        if(args.minmax):
            plt.plot(np.min(traces,axis=0), linewidth=0.1)
            plt.plot(np.max(traces,axis=0), linewidth=0.1)
        
        if(args.range):
            plt.plot(np.max(traces,axis=0) - np.min(traces,axis=0), linewidth=0.1)


    plt.tight_layout()
        
    fig.savefig(args.graph)



if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    main(build_arg_parser())
