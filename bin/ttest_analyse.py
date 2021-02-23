#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import argparse
import logging as log
import gc

from tqdm import tqdm

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
from   scass.trace import loadTracesFromDisk

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

    parser.add_argument("--trim-start",type=int,default = 0,
        help="Trim this many samples from start of graph.")
    
    parser.add_argument("--trim-end",type=int,default = 1,
        help="Trim this many samples from end of graph.")

    parser.add_argument("--abs",action="store_true",
        help="Plot the absolute value of the TTrace.")
    
    parser.add_argument("--avg",action="store_true",
        help="Plot the average trace on a separate axis.")

    parser.add_argument("--fig-width",type=float,default=9.5)
    parser.add_argument("--fig-height",type=float,default=5)
    parser.add_argument("--fig-title",type=str,default="TTest Results")

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

def butter_filter(data, cutoff, fs, btype, order=5):
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

    fbits       = loadTracesFromDisk(args.trs_fixed)
    traces      = loadTracesFromDisk(args.trs_trace)

    gc.collect()

    fixed_idx   = np.nonzero(fbits >= 1)
    rand_idx    = np.nonzero(fbits <  1)

    average_trace=np.mean(traces,axis=0)

    ts_fixed    = traces[fixed_idx]
    ts_random   = traces[ rand_idx]
    
    ts_fixed =ts_fixed[:,args.trim_start:-args.trim_end]
    ts_random=ts_random[:,args.trim_start:-args.trim_end]
    average_trace=average_trace[args.trim_start:-args.trim_end]

    gc.collect()

    nfixed = ts_fixed.shape[0]
    nrandom= ts_random.shape[0]

    if(args.low_pass):
        log.info("Running low-pass filter at %dHz"% args.low_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        for i in tqdm(range(0, nfixed)):
            ts_fixed[i] = butter_filter(
                ts_fixed[i] , args.low_pass, args.sample_rate, 'lowpass')
        for i in tqdm(range(0, nrandom)):
            ts_random[i]= butter_filter(
                ts_random[i], args.low_pass, args.sample_rate, 'lowpass')

    if(args.high_pass):
        log.info("Running high-pass filter at %dHz"% args.high_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        for i in tqdm(range(0, nfixed)):
            ts_fixed[i] = butter_filter(
                ts_fixed[i] , args.high_pass, args.sample_rate, 'highpass')
        for i in tqdm(range(0, nrandom)):
            ts_random[i]= butter_filter(
                ts_random[i], args.high_pass, args.sample_rate, 'highpass')
    
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
        fig,ax1 = plt.subplots()
        fig.set_size_inches(args.fig_width,args.fig_height,forward=True)
        plt.title(args.fig_title)
        plt.xlabel("Sample")
        plt.ylabel("T-Statistic")

        if(args.avg):
            ax2 = ax1.twinx()
            ax2.set_label("Average Power Consumption, DC blocked")
            ax2.plot(average_trace, color='green', linewidth=0.15)

        ax1.plot(
            [args.critical_value]*ttest.ttrace.size,
            linewidth=0.3,color="red"
        )

        if(args.abs):
            ax1.plot(np.abs(ttest.ttrace), linewidth=0.3)
        else:
            ax1.plot(       ttest.ttrace , linewidth=0.3)

            ax1.plot(
                [-args.critical_value]*ttest.ttrace.size,
                linewidth=0.3,color="red"
            )

        fig.tight_layout()
        fig.savefig(args.graph_ttest,bbox_inches="tight", pad_inches=0)


if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    sys.exit(main())


