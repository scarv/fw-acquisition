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
from scipy.signal import butter
from scipy.signal import lfilter
from scipy.signal import freqz

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
    
    parser.add_argument("--low-pass",type = int,
        help="Run a low pass filter before analysis at this frequency.")
    
    parser.add_argument("--high-pass",type = int,
        help="Run a high pass filter before analysis at this frequency.")
    
    parser.add_argument("--sample-rate",type = int, default=250000000,
        help="Sample rate - used for filtering.")

    parser.add_argument("--ttrace-dump",type=argparse.FileType("wb"),
        help="Dump the resulting ttrace to this file for later use.")

    parser.add_argument("--abs",action="store_true",
        help="Plot the absolute value of the TTrace.")

    parser.add_argument("trs_fixed",type=str,
        help="File path of .npy array indicating if traces are fixed or random.")

    parser.add_argument("trs_trace",type=str,
        help="File path of .npy file containing the traces")


    return parser.parse_args()

def butter_lowpass(cutoff, fs, order=5, btype='low'):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype=btype, analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, btype, order=10):
    b, a = butter_lowpass(cutoff, fs, order=order, btype=btype)
    y = lfilter(b, a, data)
    return y

def main():
    """
    Main function for the tool script
    """
    args        = parse_args()
    
    if(not os.path.isfile(args.trs_trace)):
        log.error("Input traceset %s does not exist." % args.trs_trace)
        return 1
    
    if(not os.path.isfile(args.trs_fixed)):
        log.error("Input fixed mask %s does not exist." % args.trs_fixed)
        return 2

    log.info("Decompressing traceset %s" % args.trs_trace)

    gzfh_fixed  = gzip.GzipFile(args.trs_fixed,"r")
    gzfh_traces = gzip.GzipFile(args.trs_trace,"r")

    fbits       = np.load(gzfh_fixed)
    traces      = np.load(gzfh_traces)

    fixed_idx   = np.nonzero(fbits >= 1)
    rand_idx    = np.nonzero(fbits <  1)

    ts_fixed    = traces[fixed_idx]
    ts_random   = traces[ rand_idx]

    if(args.low_pass):
        log.info("Running low-pass filter at %dHz"% args.low_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        ts_fixed = butter_lowpass_filter(
            ts_fixed , args.low_pass, args.sample_rate, 'lowpass')
        ts_random= butter_lowpass_filter(
            ts_random, args.low_pass, args.sample_rate, 'lowpass')

    if(args.high_pass):
        log.info("Running high-pass filter at %dHz"% args.high_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        ts_fixed = butter_lowpass_filter(
            ts_fixed , args.high_pass, args.sample_rate,'highpass')
        ts_random= butter_lowpass_filter(
            ts_random, args.high_pass, args.sample_rate,'highpass')

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
        fig.set_size_inches(9.5,5,forward=True)
        plt.title("TTest Results")
        plt.xlabel("Sample")
        plt.ylabel("Leakage")

        plt.plot(
            [args.critical_value]*ttest.ttrace.size,
            linewidth=0.25,color="red"
        )

        if(args.abs):
            plt.plot(np.abs(ttest.ttrace), linewidth=0.1)
        else:
            plt.plot(       ttest.ttrace , linewidth=0.1)

            plt.plot(
                [-args.critical_value]*ttest.ttrace.size,
                linewidth=0.25,color="red"
            )

        plt.tight_layout()
        plt.savefig(args.graph_ttest,bbox_inches="tight", pad_inches=0)


if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())


