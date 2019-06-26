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
    parser.add_argument("trace_set",type=argparse.FileType("rb"),
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
    parser.add_argument("--threads",type=int,default=4,
        help="Number of parallel jobs to run.")
    parser.add_argument("--convolve-len",type=int,default=0,
        help="Blur together the samples in each trace based on an N length filter.")
    parser.add_argument("--subsample-factor",type=int,default=1,
        help="Subsample traces using linear interpolation before processing.")

    parser.add_argument("--graphs",action="store_true",
        help="Write out graphs of results?")

    return parser


def cpa_process_byte(cpa, b):
    """
    Runs a CPA attack on the b'th byte using the supplied CPA object.
    """
    V            = cpa.computeV(msgbyte = b)
    H            = cpa.computeH(V)
    guess,confidence,R      = cpa.computeR(H)
    return (guess, confidence, R)


def cpa_process_byte_and_word(b, cpa_byte, cpa_word, save_path, store_graphs):

    #log.info("Computing Byte guess for byte %d" % b)
    byte_guess, byte_conf, byte_R = cpa_process_byte(cpa_byte, b)
    
    #log.info("Computing Word guess for byte %d" % b)
    word_guess, word_conf, word_R = cpa_process_byte(cpa_word, b)

    if(store_graphs):
        fig = plt.figure()
        plt.clf()

        plt.suptitle("Key guess byte/word: %s (%d) / %s (%d)" % (\
            hex(byte_guess),byte_guess,hex(word_guess),word_guess))
        
        plt.subplot(221)
        plt.plot(byte_R, linewidth=0.2)
        
        plt.subplot(222)
        plt.plot(byte_R.transpose(), linewidth=0.2)
        
        plt.subplot(223)
        plt.plot(word_R, linewidth=0.2)
        
        plt.subplot(224)
        plt.plot(word_R.transpose(), linewidth=0.2)
        
        fig.set_size_inches(20,10,forward=True)
        plt.savefig("%s/%d.png" % (save_path,b))

        fig.clf()
        plt.close(fig)

    del byte_R
    del word_R
    
    log.info("Computing guesses for byte %d - Byte: %s (%f), Word: %s (%f)" %(
        b,
        hex(byte_guess),
        byte_conf,
        hex(word_guess),
        word_conf
    ))
    
    return (byte_guess, word_guess, byte_conf, word_conf)


def main(
    args,
    analyser   = scass.cpa.CorrolationAnalysis,
    powermodel = scass.cpa.CPAModelHammingWeightD
    ):
    """
    Main function for the tool script
    """
    
    log.info("Loading traces: %s" % args.trace_set.name)
    ts_set_rd = scass.trace.TraceReaderSimple(args.trace_set)
    
    ts_set    = scass.trace.TraceSet()
    ts_set.loadFromTraceReader(ts_set_rd, n=args.max_traces)

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
    
    cpa_word = analyser(
        ts_set,
        keyBytes=args.key_bytes,
        messageBytes=args.message_bytes
    )
    
    cpa_byte.var_to_attack = "sbox_byte"
    cpa_word.var_to_attack = "sbox_word"

    if(args.max_traces):
        cpa_byte.max_traces = args.max_traces
        cpa_word.max_traces = args.max_traces

    log.info("Trace Length      : %d" % cpa_byte.T)
    log.info("Trace Count       : %d" % cpa_byte.D)
    log.info("Running with %d threads." % args.threads)
    #log.info("Aux Data Shape    : %s" % str(cpa.amat.shape))
    #log.info("Trace Data Shape  : %s" % str(cpa.tmat.shape))

    byte_guesses    = [0] * args.key_bytes
    word_guesses    = [0] * args.key_bytes
    
    byte_confidence = [0.0] * args.key_bytes
    word_confidence = [0.0] * args.key_bytes
    
    with Pool(args.threads) as p:
        
        map_arguments = zip(
            range(0, args.key_bytes),
            repeat(cpa_byte),
            repeat(cpa_word),
            repeat(args.save_path),
            repeat(args.graphs),
        )

        results = p.starmap(cpa_process_byte_and_word, map_arguments)

        for i in range(0, args.key_bytes):
            bg, wg, bc, wc      = results[i]
            byte_guesses[i]     = bg
            word_guesses[i]     = wg
            byte_confidence[i]  = bc
            word_confidence[i]  = wc

    byte_guess = array.array('B',byte_guesses).tostring().hex()
    word_guess = array.array('B',word_guesses).tostring().hex()

    log.info("Byte Confidence: %s" % str(byte_confidence))
    log.info("Word Confidence: %s" % str(word_confidence))
    
    log.info("Byte Confidence: %f" % (sum(byte_confidence)/args.key_bytes))
    log.info("Word Confidence: %f" % (sum(word_confidence)/args.key_bytes))
    
    log.info("Byte Key Guess: %s" % byte_guess)
    log.info("Word Key Guess: %s" % word_guess)

    expected_key = ""

    if(args.expected_key != ""):
        hexstr = args.expected_key
        if(hexstr.startswith("0x")):
            hexstr = hexstr[2:]
        expected_key = bytes.fromhex(hexstr)
        log.info("Expected Key  : %s" % hexstr)

        byte_distances = [0] * args.key_bytes
        word_distances = [0] * args.key_bytes

        for i in range(0, args.key_bytes):
            byte_distances[i] = cpa_byte.hd(byte_guesses[i], expected_key[i])
            word_distances[i] = cpa_word.hd(word_guesses[i], expected_key[i])

        byte_distance = sum(byte_distances)
        word_distance = sum(word_distances)

        byte_score = 100 * (1.0 - byte_distance / (8*args.key_bytes))
        word_score = 100 * (1.0 - word_distance / (8*args.key_bytes))

        log.info("Score: Byte: %03f, Word %03f" % (byte_score,word_score))

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


