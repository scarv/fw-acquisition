
"""
This file is used to attack traces we have captured using the flow
"""


import os
import sys
import logging as log

from multiprocessing import Pool

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from .SassTrace   import SassTrace   
from .SassStorage import SassStorage

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
        return "%d %s %f" % (self.byte,hex(self.value),self.confidence)


class SassAttack:
    """
    Class containing everything we need to run an attack.
    """


    def __init__(self, args):
        """
        Create a new attack class.
        """
        self.args          = args
        self.isolate_start = args.isolate_from
        self.isolate_end   = args.isolate_to
        self.tracefile     = args.trace_file
        self.bin_traces    = args.bin_traces
        self.power_lut     = self.precompute_power_estimates()

    def isolateData(self):
        """
        Responsible for iterating over all of the trace data and
        trimming away the parts of the trace we are not interested in
        analysing. Assumes that the traces are all aligned correctly
        to begin with.
        """
        
        pb = tqdm(self.storage.traces)
        pb.set_description("Isolating Traces")
        for trace in pb:
            trace.data = trace.data[self.isolate_start:self.isolate_end]
            self.storage.trace_len = len(trace.data)


    def intermediateValue(self, databyte, keybyte):
        """
        XOR the two together.
        """
        return sbox[databyte ^ keybyte]


    def estimatedPower(keybyte, databyte, intermediate):
        """
        Use a hamming weight model
        """
        tr = 0.1
        for i in range(0,8):
            tr += (intermediate >> i) & 0x1
        return float(tr)


    def precompute_power_estimates(self):
        """
        Return a 256x256 array of estimates of power comsumption for a given
        key byte an data byte.
        The array is indexed as ARRAY[key][data]
        """
        
        keys = range(0,256)
        data = range(0,256)

        return np.array(
            [[SassAttack.estimatedPower(k,d,self.intermediateValue(d,k))
                for d in data] for k in keys]
        )


    def computeEstimatedPowerValues(self, d, keybyte):
        """
        Given the D by K matrix of intermediate values, model the power
        required to compute each one.
        """
        D       = range(0, len(d))
        K       = range(0, 256)
        hvals = np.array(
            [[self.power_lut[k][d[i]] for k in K] for i in D]
        )

        return hvals


    def computeCorrelation(self, hvals, tvals):
        """
        Compute the correlation coefficients for our key guesses.
        """
        A = hvals
        B = tvals

        A_mA = A - A.mean(1)[:,None]
        B_mB = B - B.mean(1)[:,None]

        # Sum of squares across rows
        ssA = (A_mA**2).sum(1);
        ssB = (B_mB**2).sum(1);

        # Finally get corr coeff
        rvals = np.dot(A_mA,B_mB.T)/np.sqrt(np.dot(ssA[:,None],ssB[None]))
        if(self.args.average_correlations):
            rvals = np.mean(rvals,axis=1)
        return rvals


    def binTraces(self, message_byte):
        """
        From T trace/message pairs, bin into 256 message/trace pairs by
        averaging traces with the same message byte values.
        """

        d    = range(0,256)
        bins = {}
        averages = {}
        
        pb = tqdm(self.storage.traces)
        pb.set_description("Binning traces")

        for t in pb:
            databyte = t.message[message_byte]
            if(not databyte in bins.keys()):
                bins[databyte] = set([])

            bins[databyte].add(t)

        pb = tqdm(bins)
        pb.set_description("Averaging traces over bins")

        for i in pb:
            averages[i] = np.array([t.data for t in bins[i]])
            averages[i] = np.mean(averages[i],axis=0)
        
        return np.array([averages[i] for i in bins])
        
    def getCandidateForKeyByte(self, keybyte, keylen):
        """
        Responsible for running an attack on a single key byte, where
        0 <= keybyte <=keylen 
        """
        K = range(0,256)
        
        D  = len(self.storage)           # Number of encryptions (traces)
        Tb = self.storage.trace_len      # Length of each trace
        
        d = None
        T = None

        if(self.bin_traces):

            binned = self.binTraces(keybyte)
            d = np.array(range(0,256))
            T = binned
            D = 256

        else:

            d = np.array([t.message[keybyte] for t in self.storage.traces])
            T  = np.array([t.data for t in self.storage.traces])

        assert(len(d) == D)
        log.debug("Shape of d: %s" % str(d.shape))

        assert(T.shape == (D,Tb))
        log.debug("Shape of T: %s" % str(T.shape))

        
        H = self.computeEstimatedPowerValues(d, keybyte)
        assert(H.shape == (D,len(K)))
        log.debug("Shape of H: %s" % str(H.shape))

        R = self.computeCorrelation(np.transpose(H),np.transpose(T))
        log.debug("Shape of R: %s" % str(R.shape))

        if(self.args.show_correlations):
            plt.figure(1)
            plt.subplot(4,4,keybyte+1)
            plt.ylim([-0.1,0.1])
            plt.plot(R,linewidth = 0.25)
        
        candidateidx = np.unravel_index(np.argmax(R, axis=None), R.shape)
        log.debug("byte guess: %s" % hex(candidateidx[0]))

        tr = KeyEstimate(keybyte,candidateidx[0])
        return tr


    def run(self):
        """
        Run the full attack
        """
        log.info("Running attack on trace file: %s" % self.tracefile)

        self.storage = SassStorage(self.tracefile)
        log.info(self.storage.trace_description)

        self.isolateData()
        
        log.info("Loaded %d traces..." % len(self.storage))
        
        keybytes = [KeyEstimate(0,0)] * 16
       
        if(self.args.show_correlations):
            plt.ion()
            plt.show()

        pb = tqdm(range(0,16))
        pb.set_description("Guessing Key Bytes")
        for i in pb:
            keybytes[i] = self.getCandidateForKeyByte(i,16)

            keyguess = [k.value for k in keybytes]
            keyguess = bytearray(keyguess).hex()

            if(self.args.show_correlations):
                fig=plt.figure(1)
                fig.suptitle("Attacking %s - keyguess=%s" %(
                    self.tracefile,
                    keyguess
                ),fontsize=11,y=0.995)
                plt.tight_layout()
                plt.draw()
                plt.pause(0.001)


        if(self.args.show_correlations):
            plt.ioff()

        print("Final key guess: %s" % [hex(k.value) for k in keybytes])
        input("[Return] to exit")


