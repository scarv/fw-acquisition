#!/usr/bin/python3

"""
A tool script for running Corrolation Power Analysis (CPA) on
different inputs, using the hamming distance of inputs as guesses.
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
from   scass.trace import loadTracesFromDisk

def parse_args():
    """
    Parse command line arguments to the script
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("traces",type=str,
        help="File path of input trace set")
    
    parser.add_argument("inputs1",type=str,
        help="File path of input variables.")
    
    parser.add_argument("inputs2",type=str,
        help="File path of input variables.")
    
    parser.add_argument("--trace-filter-out",type=str,
        help="Filepath to Mask to filter out a subset of traces from <traces>")
    
    parser.add_argument("-l", "--logfile", type=str,default=None,
        help="Log CPA information and progress to this file.)")
    

    parser.add_argument("--dump",type=str,
        help="Write the final HW corrolation trace to this file.")

    parser.add_argument("--graph",type=str,
        help="Write plot to this file path")
    
    return parser.parse_args()

def hw(x):
    """Return hamming weight of x"""
    c = 0
    while x > 0:
        c  = c + 1
        x &= x-1
    return c

def hd(x,y):
    total = 0
    for i,j in zip(x,y):
        dist   = i ^ j
        weight = hw(dist)
        #print("%03d %03d - %08s %08s %08s" %(
        #    dist,
        #    weight,
        #    bin(i),
        #    bin(j),
        #    bin(dist),
        #))
        total += weight
    return total


def main(args):
    """
    Script main function
    """
    
    log.info("Loading traces...")
    
    traces          = loadTracesFromDisk(args.traces)
    inputs_1        = loadTracesFromDisk(args.inputs1)
    inputs_2        = loadTracesFromDisk(args.inputs2)

    if(args.trace_filter_out != None):
        log.info("Filtering traces...")
        fbits           = loadTracesFromDisk(args.trace_filter_out)
        select_idx      = np.nonzero(fbits <  1)

        traces          = traces[select_idx]
        inputs_1        = inputs_1[select_idx]
        inputs_2        = inputs_2[select_idx]
    
    D_trace_count, T_trace_len  = traces.shape

    # Key guesses are always one here, since we take values directly from
    # the input arrays.
    K_guesses                   = 1

    log.info("Trace Count   D=%d" % D_trace_count)
    log.info("Trace Length  T=%d" % T_trace_len  )
    
    T = traces
    log.info("T = DxT matrix = %d x %d" % T.shape)

    H = np.zeros((D_trace_count, K_guesses))
    log.info("H = DxK matrix = %d x %d" % H.shape)

    for i in range(0, D_trace_count):
        H[i,0] = hd(inputs_1[i] , inputs_2[i])

    H_avgs = np.mean(H,axis=0)
    T_avgs = np.mean(T,axis=0)

    #print(np.min(H))
    #print(np.max(H))
    #print(T)
    #print(T_avgs.shape)
    #print(T_avgs)
    
    R = np.zeros((K_guesses, T_trace_len))
    log.info("R = KxT matrix = %d x %d" % R.shape)

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
    
    if(args.dump):
        log.info("Dumping CPA HW trace to %s" % args.dump)
        np.save(args.dump, R.transpose())

    plt.figure(1)
    fig = plt.gcf()
    fig.set_size_inches(9.5,5,forward=True)
    plt.plot(R.transpose(),linewidth=0.1)
    plt.tight_layout()

    if(args.graph != None):
        plt.tight_layout()
        plt.savefig(args.graph,bbox_inches="tight", pad_inches=0)



if(__name__ == "__main__"):
    args = parse_args()
    log.basicConfig(level=log.INFO)
    result = main(args)
    sys.exit(result)

