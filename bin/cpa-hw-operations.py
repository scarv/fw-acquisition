#!/usr/bin/python3

"""
A tool script for running Corrolation Power Analysis (CPA) on
different inputs, using the hamming weight of inputs as guesses.
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

    parser.add_argument("traces",type=str,
        help="File path of input trace set")

    parser.add_argument("--op-add",type=str,nargs=2,
        help="File paths of operands to an addition. Check hw of result.")

    parser.add_argument("--op-sub",type=str,nargs=2,
        help="File paths of operands to a subtraction. Check hw of result.")

    parser.add_argument("--op-and",type=str,nargs=2,
        help="File paths of operands to a bitwise and. Check hw of result.")

    parser.add_argument("--op-or","--op-ior",type=str,nargs=2,
        help="File paths of operands to a bitwise or. Check hw of result.")

    parser.add_argument("--op-xor",type=str,nargs=2,
        help="File paths of operands to a bitwise xor. Check hw of result.")

    parser.add_argument("--op-not",type=str,nargs="+",
        help="File paths of operands to a bitwise not. Check hw of result.")
    

    parser.add_argument("--trace-filter-out",type=str,
        help="Filepath to Mask to filter out a subset of traces from <traces>")
    
    parser.add_argument("-l", "--logfile", type=str,default=None,
        help="Log CPA information and progress to this file.)")
    
    parser.add_argument("--low-pass",type = int,
        help="Run a low pass filter before analysis at this frequency.")
    
    parser.add_argument("--high-pass",type = int,
        help="Run a high pass filter before analysis at this frequency.")
    
    parser.add_argument("--sample-rate",type = int, default=250000000,
        help="Sample rate - used for filtering.")

    parser.add_argument("--graph",type=str,
        help="Write plot to this file path")
    
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

def hw(x):
    """Return hamming weight of x"""
    c = 0
    if(isinstance(x,np.ndarray)):
        for y in x:
            z = y
            while z > 0:
                c  = c + 1
                z &= z-1
    else:
        while x > 0:
            c  = c + 1
            x &= x-1
    return c

def get_operation_results_to_check(args):

    ops_to_check    = []

    if(args.op_add):
        lhs = np.load(gzip.GzipFile(args.op_add[0],"r"))
        rhs = np.load(gzip.GzipFile(args.op_add[1],"r"))
        ops_to_check.append(("add",{"result":lhs + rhs,"lhs":lhs,"rhs":rhs}))

    if(args.op_sub):
        lhs = np.load(gzip.GzipFile(args.op_sub[0],"r"))
        rhs = np.load(gzip.GzipFile(args.op_sub[1],"r"))
        ops_to_check.append(("sub",{"result":lhs - rhs,"lhs":lhs,"rhs":rhs}))

    if(args.op_and):
        lhs = np.load(gzip.GzipFile(args.op_and[0],"r"))
        rhs = np.load(gzip.GzipFile(args.op_and[1],"r"))
        ops_to_check.append(("and",{"result":lhs & rhs,"lhs":lhs,"rhs":rhs}))

    if(args.op_or):
        lhs = np.load(gzip.GzipFile(args.op_or[0],"r"))
        rhs = np.load(gzip.GzipFile(args.op_or[1],"r"))
        ops_to_check.append(("or",{"result":lhs | rhs,"lhs":lhs,"rhs":rhs}))

    if(args.op_xor):
        lhs = np.load(gzip.GzipFile(args.op_xor[0],"r"))
        rhs = np.load(gzip.GzipFile(args.op_xor[1],"r"))
        ops_to_check.append(("xor",{"result":lhs ^ rhs,"lhs":lhs,"rhs":rhs}))
    
    if(args.op_not):
        rhs = np.load(gzip.GzipFile(args.op_not[0],"r"))
        ops_to_check.append(("not",{"result":~rhs,"rhs":rhs}))

    return ops_to_check
    

def get_hamming_weight(inputs,traces):
    D_trace_count, T_trace_len  = traces.shape

    # Key guesses are always one here, since we take values directly from
    # the input arrays.
    K_guesses                   = 1

    log.debug("Trace Count   D=%d" % D_trace_count)
    log.debug("Trace Length  T=%d" % T_trace_len  )
    
    T = traces
    log.debug("T = DxT matrix = %d x %d" % T.shape)

    H = np.zeros((D_trace_count, K_guesses))
    log.debug("H = DxK matrix = %d x %d" % H.shape)

    for i in range(0, D_trace_count):
        H[i,0] = hw(inputs[i])

    H_avgs = np.mean(H,axis=0)
    T_avgs = np.mean(T,axis=0)
    
    R = np.zeros((K_guesses, T_trace_len))
    log.debug("R = KxT matrix = %d x %d" % R.shape)

    for i in range(0,K_guesses):

        H_avg   = H_avgs[i]
        H_col   = H[:,i]
        H_col_d = H_col - H_avg
    
        H_col_sq_sum = np.dot(H_col_d,H_col_d)

        for j in range(0, T_trace_len):

            T_avg   = T_avgs[j]
            T_col   = traces[:D_trace_count,j]
            T_col_d = T_col - T_avg
            T_col_sq_sum = np.dot(T_col_d, T_col_d)

            top = np.dot(H_col_d, T_col_d)

            bot = np.sqrt(H_col_sq_sum * T_col_sq_sum)
            if(bot == 0):
                bot = 1

            R[i,j] = np.abs(top/bot)

    return R


def main(args):
    """
    Script main function
    """

    log.info("Loading traces...")
    
    gzfh_traces     = gzip.GzipFile(args.traces,"r")
    traces          = np.load(gzfh_traces)

    to_check = get_operation_results_to_check(args)

    if(args.trace_filter_out != None):
        log.info("Filtering traces...")
        gzfh_filter_out = gzip.GzipFile(args.trace_filter_out,"r")
        fbits           = np.load(gzfh_filter_out)
        select_idx      = np.nonzero(fbits <  1)

        traces          = traces[select_idx]

        for t in to_check:
            name, values = t
            for k in values:
                values[k] = values[k][select_idx]


    if(args.low_pass):
        log.info("Running low-pass filter at %dHz"% args.low_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        traces = butter_lowpass_filter(
            traces, args.low_pass, args.sample_rate, 'lowpass')

    if(args.high_pass):
        log.info("Running high-pass filter at %dHz"% args.high_pass)
        log.info("Sample rate set at: %dHz"% args.sample_rate)
        traces = butter_lowpass_filter(
            traces, args.high_pass, args.sample_rate,'highpass')
    
    plt.figure(1)
    fig = plt.gcf()
    fig.set_size_inches(9.5,5,forward=True)

    for t in to_check:
        name, values = t
        for v in values:
            label   = "%s-%s" % (name, v)
            log.info("Calculating hamming weight for %s"%(label))
            R       = get_hamming_weight(values[v],traces)
            plt.plot(R.transpose(),linewidth=0.1,label=label)

    plt.legend()
    plt.tight_layout()

    if(args.graph != None):
        plt.tight_layout()
        plt.savefig(args.graph,bbox_inches="tight", pad_inches=0)


if(__name__ == "__main__"):
    args = parse_args()
    log.basicConfig(level=log.INFO)
    result = main(args)
    sys.exit(result)

