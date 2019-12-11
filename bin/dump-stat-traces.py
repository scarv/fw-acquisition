#!/usr/bin/python3

"""
A script for dumping statistic traces from much larger trace sets.
Makes working with things like the average trace much easier.
"""

import os
import sys
import secrets
import argparse
import logging as log

import gzip
import numpy as np

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

    parser.add_argument("--avg-trace", type=str,
        help="Dump average trace of set to this file.")

    parser.add_argument("--stddev", type=str,
        help="Dump standard deviation of all traces to this file.")

    parser.add_argument("--min", type=str,
        help="Dump minimum over time of every trace to this file.")
    
    parser.add_argument("--max", type=str,
        help="Dump maximum over time of every trace to this file.")

    parser.add_argument("--range", type=str,
        help="Dump range between min/max point over every trace to this file.")

    parser.add_argument("traceset",type=str,
        help="The set of traces to analyse")
    
    return parser

def main(argparser):
    """
    Script main function
    """
    args = argparser.parse_args()

    if(not os.path.isfile(args.traceset)):
        log.error("Input traceset %s does not exist." % args.traceset)
        return 1
        
    log.info("Decompressing traceset %s" % args.traceset)
    gzfh   = gzip.GzipFile(args.traceset,"r")
    traces = np.load(gzfh)

    if(args.avg_trace):
        log.info("Saving average trace to %s" % args.avg_trace)
        np.save(args.avg_trace, np.mean(traces,axis=0))

    if(args.stddev):
        log.info("Saving stddev trace to %s" % args.stddev)
        np.save(args.stddev, np.std(traces,axis=0))
    
    if(args.min):
        log.info("Saving min trace to %s" % args.min)
        np.save(args.min, np.min(traces,axis=0))

    if(args.max):
        log.info("Saving max trace to %s" % args.max)
        np.save(args.max, np.max(traces,axis=0))
    
    if(args.range):
        log.info("Saving range trace to %s" % args.range)
        rng = np.max(traces,axis=0) - np.min(traces,axis=0)
        np.save(args.range, rng)


if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    ap = build_arg_parser()
    sys.exit(main(ap))
