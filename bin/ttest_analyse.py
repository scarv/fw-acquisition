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
    
    parser.add_argument("--graph-t-over-n",type=str, default = None,
        help="If set, write max T value v.s. num traces graph to this file")
    
    parser.add_argument("--graph-avg-trace",type=str, default = None,
        help="If set, write the average traces for each set to this file")

    parser.add_argument("--critical-value",type=float,default=4.5,
        help="Critical value for TTest threshold")

    parser.add_argument("--second-order",action="store_true",default=False,
        help="Do a second order TTest.")

    parser.add_argument("--ttrace-dump",type=argparse.FileType("wb"),
        help="Dump the resulting ttrace to this file for later use.")
    
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

    if(args.graph_t_over_n):
        raise NotImplementedError("t over n graphs not yet implemented")
        log.info("Writing T-over-N graph: %s" % args.graph_t_over_n)
        plt.clf()
        fig = plt.gcf()
        plt.tight_layout
        plt.title("Max-T over N traces")
        plt.xlabel("Traces")
        plt.ylabel("Peak Leakage")

        tti = scass.ttest.TTestIncremental(second_order = args.second_order)

        tti.ingest(ts_fixed, ts_random)

        plt.plot(tti.t_over_time, tti.n_over_time,
            linewidth="0.25", color="blue")

        plt.plot(
            [args.critical_value]*ttest.ttrace.size,
            linewidth=0.25,color="red"
        )

        fig.set_size_inches(10,5,forward=True)
        plt.savefig(args.graph_t_over_n,bbox_inches="tight", pad_inches=0)

    if(args.graph_avg_trace):
        log.info("Writing Average Traces Graph: %s" % args.graph_avg_trace)
        plt.clf()
        fig,ax=plt.subplots()
        plt.tight_layout
        plt.title("Average Traces")
        plt.xlabel("Sample")
        plt.ylabel("Power Variation")
        plt.plot(ts_fixed.averageTrace() ,linewidth=0.1,label="Fixed")
        plt.plot(ts_random.averageTrace(),linewidth=0.1,label="Random")
        fig.set_size_inches(10,5,forward=True)
        legend=ax.legend(loc="upper right")
        plt.savefig(args.graph_avg_trace,bbox_inches="tight", pad_inches=0)
    

if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())


