#!/usr/bin/python3

"""
A tool script for running Corrolation Power Analysis (CPA) on
different inputs, using the hamming distance of inputs as guesses.
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

def main(args):
    """
    Script main function
    """
    
    if(args.logfile != None):
        log.basicConfig(filename=args.logfile, filemode="w",level=log.DEBUG)
    else:
        log.basicConfig(level=log.DEBUG)
    log.getLogger().addHandler(log.StreamHandler())

    log.info("Loading traces...")
    
    gzfh_traces     = gzip.GzipFile(args.traces,"r")
    traces          = np.load(gzfh_traces)
    
    gzfh_inputs_1   = gzip.GzipFile(args.inputs1,"r")
    inputs_1        = np.load(gzfh_inputs_1)
    
    gzfh_inputs_2   = gzip.GzipFile(args.inputs2,"r")
    inputs_2        = np.load(gzfh_inputs_2)

    if(args.trace_filter_out != None):
        log.info("Filtering traces...")
        gzfh_filter_out = gzip.GzipFile(args.trace_filter_out,"r")
        fbits           = np.load(gzfh_filter_out)
        select_idx      = np.nonzero(fbits <  1)

        traces          = traces[select_idx]
        inputs_1        = inputs_1[select_idx]
        inputs_2        = inputs_2[select_idx]

    trace_count, trace_len = traces.shape
    input_count            = inputs_1.shape[0]

    assert(inputs_1.shape == inputs_2.shape)

    log.info("Input Count   : %d" % input_count)
    log.info("Trace Count   : %d" % trace_count)
    log.info("Trace Length  : %d" % trace_len  )
    
    H = np.zeros(inputs_1.shape)

    for i in range(0, input_count):
        H[i] = hw(inputs_1[i] ^ inputs_2[i])

    H_avgs = np.mean(H,axis=0)
    T_avgs = np.mean(traces,axis=0)
        
    R_shape = (1, trace_len)
    R       = np.empty(R_shape, dtype = np.float32, order='C')

   
    for i in range(0,1):

        H_avg   = H_avgs[i]
        H_col   = H[:,i]
        H_col_d = H_col - H_avg
    
        H_col_sq_sum = np.dot(H_col_d,H_col_d)

        for j in range(0, trace_len):

            T_avg   = T_avgs[j]
            T_col   = traces[:trace_count,j]
            T_col_d = T_col - T_avg
            T_col_sq_sum = np.dot(T_col_d, T_col_d)
        
            #log.info("T_col    Shape: %s" % str(T_col   .shape))
            #log.info("T_col_d  Shape: %s" % str(T_col_d .shape))

            top = np.dot(H_col_d, T_col_d)

            bot = np.sqrt(H_col_sq_sum * T_col_sq_sum)
            if(bot == 0):
                bot = 1

            R[i,j] = np.abs(top/bot)


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
    result = main(args)
    sys.exit(result)

