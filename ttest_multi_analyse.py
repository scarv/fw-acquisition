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
    
    parser.add_argument("--graph-avg-random-trace",type=str, default = None,
        help="If set, write the average random traces for each set to this file")
    
    parser.add_argument("--graph-avg-fixed-trace",type=str, default = None,
        help="If set, write the average fixed traces for each set to this file")

    parser.add_argument("--critical-value",type=float,default=4.5,
        help="Critical value for TTest threshold")
    
    parser.add_argument("-t","--trace-set",nargs=3,action="append",
        help="Add a TTest trace set to be included in the analysis. "+\
             "Should be of the form: -s <name> <fixed> <random>. "+\
             "Where: <name> is the name of the set,"+\
             "<fixed> is the path to the fixed traces file and"+\
             "<random> is the path to the random traces file")

    return parser.parse_args()

def graph_traces(title,xaxis,yaxis, collection):
    """
    Create and return a matplotlib figure with all of the
    traces plotted on a graph.

    parameters:
    -----------
    collection - A list of tuples of the form
        (trace label, trace)
    """

    fig = plt.figure()
    fig.clf()

    fig.suptitle(title)

    axes    = fig.gca()
    
    axes.set_xlabel(xaxis)
    axes.set_ylabel(yaxis)

    for tset in collection:
        
        name,ttrace = tset

        axes.plot(ttrace,linewidth=0.5,label=name)
    
    legend  = axes.legend(loc="upper right")

    fig.tight_layout()
    
    fig.set_size_inches(10,5,forward=True)

    return fig


def main():
    """
    Main function for the tool script
    """
    args        = parse_args()
    
    collections = []

    log.info("Loading trace sets...")

    for name, f_path, r_path in args.trace_set:
        log.info("%15s %s %s" % (name,f_path,r_path))

        fh_fixed    = open(f_path, "rb")
        fh_random   = open(r_path, "rb")
    
        ts_fixed_rd = scass.trace.TraceReaderSimple(fh_fixed)
        ts_fixed    = scass.trace.TraceSet()
        ts_fixed.loadFromTraceReader(ts_fixed_rd)

        ts_random_rd= scass.trace.TraceReaderSimple(fh_random)
        ts_random   = scass.trace.TraceSet()
        ts_random.loadFromTraceReader(ts_random_rd)

        ttest       = scass.ttest.TTest(ts_fixed, ts_random)

        fh_fixed.close()
        fh_random.close()
        
        toadd       = (
            name,
            ttest.ttrace,
            ts_fixed.averageTrace(),
            ts_random.averageTrace()
        )

        collections.append(toadd)
    

    if(args.graph_ttest):
        log.info("Creating T-Statistic Graph...")
        ttraces = [(n[0],n[1]) for n in collections]
        fig = graph_traces(
            "T-Statistic Trace",
            "Sample",
            "T-Value",
            ttraces
        )
        plt.savefig(args.graph_ttest)

    if(args.graph_avg_random_trace):
        log.info("Creating Average Random Traces Graph...")
        ttraces = [(n[0],n[3]) for n in collections]
        fig = graph_traces(
            "Average Random Traces",
            "Sample",
            "Power Variation",
            ttraces
        )
        plt.savefig(args.graph_avg_random_trace)

    if(args.graph_avg_fixed_trace):
        log.info("Creating Average Fixed Traces Graph...")
        ttraces = [(n[0],n[3]) for n in collections]
        fig = graph_traces(
            "Average Fixed Traces",
            "Sample",
            "Power Variation",
            ttraces
        )
        plt.savefig(args.graph_avg_fixed_trace)
    

if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())



