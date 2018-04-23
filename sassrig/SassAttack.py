
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
        return databyte ^ keybyte


    def estimatedPower(keybyte, databyte, intermediate):
        """
        Use a hamming weight model
        """
        tr = 0.0
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
            [[self.power_lut[k][d[i][keybyte]] for k in K] for i in D]
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


        d = np.array([t.message for t in self.storage.traces])
        assert(len(d) == D)
        log.debug("Shape of d: %s" % str(d.shape))
        
        T  = np.array([t.data for t in self.storage.traces])
        assert(T.shape == (D,Tb))
        log.debug("Shape of T: %s" % str(T.shape))

        
        H = self.computeEstimatedPowerValues(d, keybyte)
        assert(H.shape == (D,len(K)))
        log.debug("Shape of H: %s" % str(H.shape))

        R = self.computeCorrelation(np.transpose(H),np.transpose(T))
        log.debug("Shape of R: %s" % str(R.shape))

        if(self.args.show_correlations):
            plt.figure(1)
            plt.clf()
            plt.plot(R,linewidth = 0.25)
            plt.draw()
            plt.pause(0.001)
        
        candidateidx = np.unravel_index(np.argmax(R, axis=None), R.shape)
        log.debug("byte guess: %s" % hex(candidateidx[0]))

        return candidateidx[0]


    def run(self):
        """
        Run the full attack
        """
        log.info("Running attack on trace file: %s" % self.tracefile)

        self.storage = SassStorage(self.tracefile)

        self.isolateData()
        
        log.info("Loaded %d traces..." % len(self.storage))
        
        keybytes = [-1] * 15
       
        if(self.args.show_correlations):
            plt.ion()
            plt.show()

        pb = tqdm(range(0,15))
        pb.set_description("Guessing Key Bytes")
        for i in pb:
            keybytes[i] = hex(self.getCandidateForKeyByte(i,16))

        if(self.args.show_correlations):
            plt.ioff()

        print("Final key guess: %s" % keybytes)


