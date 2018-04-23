
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
        self.isolate_start = 0
        self.isolate_end   = 11000
        self.tracefile     = args.trace_file


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


    def estimatedPower(value):
        """
        Use a hamming weight model
        """
        tr = 0
        for i in range(0,8):
            tr += (value >> i) & 0x1
        return float(tr)


    def computeIntermediateValues(self, d , keybyte):
        """
        Returns the D by K matrix of intermediate values, where D is the
        possible data value, and K is the number of possible choices for K.
        """
        K = range(0,255)
        D = range(0,len(d))
        V = np.array(
            [[self.intermediateValue(d[i][keybyte],K[k]) for k in K] for i in D]
        )

        return V


    def computeEstimatedPowerValues(self, ivals):
        """
        Given the D by K matrix of intermediate values, model the power
        required to compute each one.
        """
        D,K   = ivals.shape
        ep    = np.vectorize(SassAttack.estimatedPower, otypes=[np.float])
        hvals = ep(ivals)

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


    def getCandidateForKeyByte(self, keybyte, keylen):
        """
        Responsible for running an attack on a single key byte, where
        0 <= keybyte <=keylen 
        """
        K = range(0,255)
        
        D  = len(self.storage)           # Number of encryptions (traces)
        Tb = self.storage.trace_len      # Length of each trace

        d = np.array([t.message for t in self.storage.traces])
        assert(len(d) == D)
        log.debug("Shape of d: %s" % str(d.shape))
        
        T  = np.array([t.data for t in self.storage.traces])
        assert(T.shape == (D,Tb))
        log.debug("Shape of T: %s" % str(T.shape))

        V  = self.computeIntermediateValues(d, keybyte)
        assert(V.shape == (D,len(K)))
        log.debug("Shape of V: %s" % str(V.shape))
        
        H = self.computeEstimatedPowerValues(V)
        assert(H.shape == (D,len(K)))
        log.debug("Shape of H: %s" % str(H.shape))

        R = self.computeCorrelation(np.transpose(H),np.transpose(T))
        log.debug("Shape of R: %s" % str(R.shape))

        plt.figure(1)
        plt.plot(R,linewidth = 0.05)
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
       
        plt.ion()
        plt.show()

        pb = tqdm(range(0,15))
        pb.set_description("Guessing Key Bytes")
        for i in pb:
            keybytes[i] = hex(self.getCandidateForKeyByte(i,16))

        plt.ioff()

        log.info("Final key guess: %s" % keybytes)


