#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import array
import argparse
import logging as log

from itertools       import repeat
from multiprocessing import Pool

import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

import scass
    
argparser = argparse.ArgumentParser()

def parse_args(parser):
    """
    Parse command line arguments to the script
    """
    parser.add_argument("--trace-set",type=argparse.FileType("rb"),
        help="File path to load trace set from")
    parser.add_argument("--key-bytes",type=int, default=16,
        help="Number of key bytes to guess")
    parser.add_argument("--message-bytes",type=int, default=16,
        help="Number of message bytes per block")
    parser.add_argument("--save-path", type=str, default=".",
        help="Where to save figures too.")
    parser.add_argument("--log", type=str, default="",
        help="Log file path for the attack")
    parser.add_argument("--expected-key",type=str, default="",
        help="A hex string representing the expected key value to find in the attack")
    parser.add_argument("--max-traces",type=int,default=None,
        help="Maximum number of traces from the set to include in the attack")
    parser.add_argument("--max-samples",type=int,default=None,
        help="Maximum number of samples from the start of a trace to consider.")
    parser.add_argument("--threads-byte",type=int,default=1,
        help="Number of key bytes to attack in parallel")
    parser.add_argument("--threads-corrolation",type=int,default=1,
        help="Number of threads to use in computing corrolation matrix.")

    parser.add_argument("--convolve-len",type=int,default=0,
        help="Blur together the samples in each trace based on an N length filter.")
    parser.add_argument("--subsample-factor",type=int,default=1,
        help="Subsample traces using linear interpolation before processing.")
    
    parser.add_argument("--only-guess-first",type=int,default=16,
        help="Only guess the first N bytes of the key.")

    parser.add_argument("--trim-last",type=int,default=0,
        help="Trim last N samples from every trace")

    parser.add_argument("--graphs",action="store_true",
        help="Write out graphs of results?")

    return parser

def write_graphs(byte_guess, byte_R, save_path, b):
    fig = plt.figure()
    plt.clf()

    plt.suptitle("Key guess byte: %s (%d)" % (\
        hex(byte_guess),byte_guess,))
    
    plt.subplot(211)
    plt.plot(byte_R, linewidth=0.2)
    
    plt.subplot(212)
    plt.plot(byte_R.transpose(), linewidth=0.2)
    
    fig.set_size_inches(20,10,forward=True)
    plt.savefig("%s/%d.png" % (save_path,b))

    fig.clf()
    plt.close(fig)

def cpa_process_byte(b, cpa_byte, save_path, store_graphs, byteCallback):

    #log.info("Computing Byte guess for byte %d" % b)
    V                               = cpa_byte.computeV(b)
    H                               = cpa_byte.computeH(V,b)
    byte_guess, byte_conf, byte_R   = cpa_byte.computeR(H)


    if(byteCallback != None):
        byteCallback(b, byte_guess, byte_conf, byte_R, save_path,cpa_byte)
    
    if(store_graphs):
        write_graphs(byte_guess, byte_R, save_path, b)

    del byte_R
    
    log.info("Computing guesses for byte %d - Byte: %s (%f)" %(
        b,
        hex(byte_guess),
        byte_conf
    ))
    
    return (byte_guess, byte_conf)


def main(
    args,
    analyser   = scass.cpa.CorrolationAnalysis,
    powermodel = scass.cpa.CPAModelHammingWeightD,
    byteCallback = None
    ):
    """
    Main function for the tool script
    """
    
    log.info("Loading traces: %s" % args.trace_set.name)
    ts_set_rd = scass.trace.TraceReaderSimple(args.trace_set)
    
    ts_set    = scass.trace.TraceSet()
    ts_set.loadFromTraceReader(ts_set_rd, n=args.max_traces)

    if(args.trim_last >0):
        log.info("Triming last %d samples from each trace." % args.trim_last)
        ts_set.trimTraces(ts_set.trace_length-args.trim_last)

    bytes_to_guess = min(args.key_bytes, args.only_guess_first)

    if(args.max_samples):
        log.info("Trimming traces to max %d samples" % args.max_samples)
        ts_set.trimTraces(args.max_samples)

    if(args.graphs):
        log.info("Will save graphs")

    if(args.convolve_len > 0):
        log.info("Convolving traces with %d-long filter..."%args.convolve_len)
        ts_set.convolveTracesUniform(args.convolve_len)

    if(args.subsample_factor > 1):
        log.info("Subsampling traces with %d factor..."%args.subsample_factor)
        ts_set.subsampleTraces(args.subsample_factor)

    cpa_byte = analyser(
        ts_set,
        keyBytes=args.key_bytes,
        messageBytes=args.message_bytes
    )
    
    cpa_byte.num_threads = args.threads_corrolation

    if(args.max_traces):
        cpa_byte.max_traces = args.max_traces

    total_threads = args.threads_byte * args.threads_corrolation
    
    log.info("Guessing upto %d bytes" % bytes_to_guess)
    log.info("Trace Length      : %d" % cpa_byte.T)
    log.info("Trace Count       : %d" % cpa_byte.D)
    log.info("Parallelism:")
    log.info("- Attacking %d bytes in parallel." % args.threads_byte)
    log.info("- Using %d Threads per byte." % args.threads_corrolation)
    log.info("- Using %d threads at a time." % total_threads)
    #log.info("Aux Data Shape    : %s" % str(cpa.amat.shape))
    #log.info("Trace Data Shape  : %s" % str(cpa.tmat.shape))

    byte_guesses    = [0] * bytes_to_guess
    
    byte_confidence = [0.0] * bytes_to_guess
       
    map_arguments = zip(
        range(0, bytes_to_guess),
        repeat(cpa_byte),
        repeat(args.save_path),
        repeat(args.graphs),
        repeat(byteCallback),
    )

    if(args.threads_byte == 1):

        for b,c,s,g,cb in map_arguments:
            guess,conf = cpa_process_byte(b,c,s,g,cb)
            byte_guesses[b] = guess
            byte_confidence[b] = conf

    else:
    
        with Pool(args.threads_byte) as p:

            results = p.starmap(cpa_process_byte, map_arguments)

            for i in range(0, bytes_to_guess):
                bg, bc              = results[i]
                byte_guesses[i]     = bg
                byte_confidence[i]  = bc

    byte_guess = array.array('B',byte_guesses).tostring().hex()

    log.info("Byte Confidence: %s" % str(byte_confidence))
    
    log.info("Byte Confidence: %f" % (sum(byte_confidence)/bytes_to_guess))
    
    log.info("Byte Key Guess: %s" % byte_guess)

    expected_key = ""

    if(args.expected_key != ""):
        hexstr = args.expected_key
        if(hexstr.startswith("0x")):
            hexstr = hexstr[2:]
        expected_key = bytes.fromhex(hexstr)
        log.info("Expected Key  : %s" % hexstr)

        byte_distances = [0] * bytes_to_guess

        for i in range(0, bytes_to_guess):
            byte_distances[i] = cpa_byte.hd(byte_guesses[i], expected_key[i])

        byte_distance = sum(byte_distances)

        byte_score = 100 * (1.0 - byte_distance / (8*bytes_to_guess))

        log.info("Score: Byte: %03f" % byte_score)

    log.info("--- Finish ---")
    

if(__name__ == "__main__"):
    args        = parse_args(argparser).parse_args()
    if(args.log != ""):
        log.basicConfig(filename=args.log,filemode="w",level=log.INFO,
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')
    else:
        log.basicConfig(level=log.INFO,
            format='%(asctime)s %(levelname)-8s %(message)s',
          datefmt='%Y-%m-%d %H:%M:%S')
    log.getLogger().addHandler(log.StreamHandler(sys.stdout))
    sys.exit(main(args))


