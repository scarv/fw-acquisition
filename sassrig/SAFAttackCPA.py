
"""
This file is used to attack traces we have captured using the flow
"""


import os
import gc
import sys
import logging as log

from multiprocessing import Pool

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from .SAFTraceSet import SAFTraceSet

sbox = [
  0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b,
  0xfe, 0xd7, 0xab, 0x76, 0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
  0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 0xb7, 0xfd, 0x93, 0x26,
  0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
  0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2,
  0xeb, 0x27, 0xb2, 0x75, 0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
  0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84, 0x53, 0xd1, 0x00, 0xed,
  0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
  0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f,
  0x50, 0x3c, 0x9f, 0xa8, 0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
  0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 0xcd, 0x0c, 0x13, 0xec,
  0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
  0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14,
  0xde, 0x5e, 0x0b, 0xdb, 0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
  0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79, 0xe7, 0xc8, 0x37, 0x6d,
  0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
  0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f,
  0x4b, 0xbd, 0x8b, 0x8a, 0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
  0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e, 0xe1, 0xf8, 0x98, 0x11,
  0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
  0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f,
  0xb0, 0x54, 0xbb, 0x16]

class KeyEstimate:
    """
    Class containing information on a key byte guess
    """

    def __init__(self, byte, value):
        self.byte = byte
        self.value = value
        self.confidence = None

    def __str__(self):
        return "%s %s %s" % (str(self.byte),str(self.value),str(self.confidence))

class SAFAttackArgs(object):
    def __init__(self):
        self.isolate_from = 0
        self.isolate_to   = -1
        self.average_correlations = False
        self.show_correlations  = False


def hamming_weight(b):
    """
    Return the hamming weight of the byte b.
    """
    return  (b & (0x1 << 0)) + \
            (b & (0x1 << 1)) + \
            (b & (0x1 << 2)) + \
            (b & (0x1 << 3)) + \
            (b & (0x1 << 4)) + \
            (b & (0x1 << 5)) + \
            (b & (0x1 << 6)) + \
            (b & (0x1 << 7)) 

class SAFAttackCPA:
    """
    Class containing everything we need to run an attack.
    """


    def __init__(self, args,trace_file):
        """
        Create a new attack class.
        """
        self.args          = args
        self.isolate_start = args.isolate_from
        self.isolate_end   = args.isolate_to
        self.tracefile     = trace_file

    def _get_power_estimates(self, d):
        """
        :param byte d: Data byte index
        """
        tr = np.empty((self.storage.num_traces,256),dtype=np.float32)
        
        # tr is (num_traces by 256) matrix
        #   tr[x,y] = intermediate_value(message[x][d], y)
        for x in range(0, self.storage.num_traces):

            plaintext_byte = self.storage.plaintexts[x][d]

            for key_byte_guess in range(0, 255):
                
                intermediate_val = sbox[plaintext_byte ^ key_byte_guess]

                tr[x,key_byte_guess] = float(hamming_weight(intermediate_val))

        return tr

    def getCandidateForKeyByte(self, keybyte ):
        """
        Responsible for running an attack on a single key byte

        K = choices for key bytes (256)
        T = samples per trace
        D = number of traces / plaintexts.
        """
        
        K = 256
        D = self.storage.num_traces
        T = self.storage.trace_length
        
        # D x T  - 
        mT = self.storage.traces[:,self.isolate_start:self.isolate_end]

        sample_len = mT.shape[1]

        # 256 power estimates per row.
        # 1 row per sample
        self.mH = self._get_power_estimates(keybyte) # D x K

        # R.shape should be (K,T)
        
        fig = plt.figure(2)
        plt.clf()

        for i in tqdm(range(0,K)):

            for j in range(0,sample_len):

                col_H = self.mH[:,i] - np.mean(self.mH[:,i])
                col_T = mT[:,j] - np.mean(mT[:,j])

                top = np.dot(col_H,col_T)

                col_T *= col_T
                col_H *= col_H

                col_T = np.sum(col_T)
                col_H = np.sum(col_H)

                bot = np.sqrt(col_T * col_H)

                self.R[i,j] = abs(top/bot)

        plt.plot(self.R,linewidth=0.25)
        plt.show()
        plt.draw()
        plt.pause(0.001)

        candidateidx = np.unravel_index(np.argmax(self.R, axis=None), self.R.shape)

        return KeyEstimate(keybyte,candidateidx[0])
        

    def run(self):
        """
        Run the full attack. Return the grah of results.
        """

        self.storage = SAFTraceSet.LoadTRS(self.tracefile)

        print("Trace Set Description:")
        print(self.storage.trace_description)
        
        keybytes = [KeyEstimate(0,0)] * 16

        print("Trace length: %d"%self.storage.trace_length)
        print("Num Traces:   %d"%self.storage.num_traces)
        
        self.R = np.empty((256,self.storage.trace_length), np.float64)

        plt.ion()
        
        print("Running...")
        for k in tqdm(range(0,16)):
            keybytes[k] = self.getCandidateForKeyByte( k)

        plt.ioff()

        print("Final key guess: %s" % [str(k.value) for k in keybytes])

        return None

