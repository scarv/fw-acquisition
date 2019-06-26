#!/usr/bin/python3

"""
A tool script for running ttests on captured data.
"""

import os
import sys
import array
import argparse
import logging as log

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

    return parser


def cpa_process_byte(cpa, b):
    """
    Runs a CPA attack on the b'th byte using the supplied CPA object.
    """
    V            = cpa.computeV(msgbyte = b)
    H            = cpa.computeH(V)
    guess,R      = cpa.computeR(H)
    return (guess, R)

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
    ts_set.loadFromTraceReader(ts_set_rd)

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
    #log.info("Aux Data Shape    : %s" % str(cpa.amat.shape))
    #log.info("Trace Data Shape  : %s" % str(cpa.tmat.shape))

    byte_guesses = []
    word_guesses = []

    for b in tqdm(range(0, args.key_bytes)):
        
        byte_guess, byte_R = None, None
        word_guess, word_R = None, None

        with Pool(2) as p:
            
            process_args = [
                (cpa_byte,b),
                (cpa_word,b)
            ]
            
            results = p.starmap(cpa_process_byte,process_args)

            byte_results = results[0]
            word_results = results[1]

            byte_guess, byte_R = byte_results
            word_guess, word_R = word_results
        
        byte_guesses.append(byte_guess)
        word_guesses.append(word_guess)

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
        plt.savefig("%s/%d.png" % (args.save_path,b))


    byte_guess = array.array('B',byte_guesses).tostring().hex()
    word_guess = array.array('B',word_guesses).tostring().hex()
    
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
        log.basicConfig(filename=args.log,filemode="w",level=log.INFO)
    else:
        log.basicConfig(level=log.INFO)
    sys.exit(main(args))


