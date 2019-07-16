
import logging as log
import time

from itertools       import repeat
from multiprocessing import Pool

import numpy as np

from tqdm import tqdm

from ..trace.TraceSet import TraceSet

from .AES import sbox as aes_sbox


def parallel_compute_R(H, T, tlen, H_avgs, T_avgs, i,numtraces):

    R_shape = (1, tlen)
    R       = np.empty(R_shape, dtype = np.float32, order='C')

    H_avg   = H_avgs[i]
    H_col   = H[:,i]
    H_col_d = H_col - H_avg
    H_col_sq_sum = np.dot(H_col_d,H_col_d)

    #log.info("H_col    Shape: %s" % str(H_col   .shape))
    #log.info("H_col_d  Shape: %s" % str(H_col_d .shape))

    for j in range(0,tlen):

        T_avg   = T_avgs[j]
        T_col   = T[:numtraces,j]
        T_col_d = T_col - T_avg
        T_col_sq_sum = np.dot(T_col_d, T_col_d)
    
        #log.info("T_col    Shape: %s" % str(T_col   .shape))
        #log.info("T_col_d  Shape: %s" % str(T_col_d .shape))

        top = np.dot(H_col_d, T_col_d)

        bot = np.sqrt(H_col_sq_sum * T_col_sq_sum)
        if(bot == 0):
            bot = 1

        R[0,j] = np.abs(top/bot)

    return R


class CorrolationAnalysis(object):
    """
    A class for performing corrolation based analysis on sets of
    traces.
    """

    def __init__(self, traces, K = 256, keyBytes = 16, messageBytes=16):
        """
        Create a new CorrolationAnalysis object which will operate
        on the supplied traces.

        parameters:
        ----------
        traces - TraceSet
            The set of traces to work with
        K - int
            Number of possible key hypotheses to consider
        keyBytes - int
            Number of bytes per key
        messageBytes - int
            Number of bytes per message
        """

        self.tmat   = traces.tracesAs2dArray().transpose()
        self.amat   = traces.auxDataAs2dArray()
        self._tnum  = traces.num_traces
        self._tlen  = traces.trace_length

        self.max_traces = self._tnum

        self._num_threads = 1

        # split key and message into two different chunks
        self.keymat = self.amat[:, 0:keyBytes]
        self.msgmat = self.amat[:,keyBytes:keyBytes+messageBytes]

        self.type_V = np.uint32
        self.type_H = np.uint32

        self._k     = K


    def _computeV(self, d, k_guess, V,i,j):
        """
        Computes the intermedate value for a given message byte d
        and key byte guess k_guess.
        """
        try:
            return aes_sbox[d^k_guess]
        except:
            print(hex(d  ))
            print(hex(k_guess  ))
            print(hex(d^k_guess))

    def computeV(self, msgbyte):
        """
        Compute the matrix of possible intermediate values to attack for
        a given set of key hypotheses.

        Returns:
            A DxK matrix of values.
        """
        V_shape = (self.D, self.K)
        V       = np.empty(V_shape, dtype=self.type_V, order='C')

        for i in tqdm(range(0,self.D)):
            for j in range(0,self.K):
                msgb   = self.msgmat[i,msgbyte]
                V[i,j] = self._computeV(msgb,j,V,i,msgbyte)

        return V

    def hw(self, x):
        """Return hamming weight of x"""
        c = 0
        while x > 0:
            c  = c + 1
            x &= x-1
        return c

    def hd(self, x, y):
        """Return hamming distance between x and y"""
        return self.hw(x ^ y)

    def computeH(self, V, msgbyte):
        """
        Compute the hypothesised power consumption values from
        the V matrix.
        """
        H_shape = (self.D, self.K)
        H       = np.empty(H_shape, dtype=self.type_H, order='C')
        
        for i in tqdm(range(0,self.D)):
            for j in range(0,self.K):
                ib = V[i,j]
                
                # Just do hamming weight for now.
                H[i,j] = self.hw(ib)

        return H

    def computeR(self, H):
        """
        Compute the matrix of correlation coefficients for each
        hypothesis.
        """

        R_shape = (self.K, self.T)
        R       = np.empty(R_shape, dtype = np.float32, order='C')

        T       = self.tmat

        H_avgs  = np.mean(H, axis=0)
        T_avgs  = np.mean(T, axis=0)

        #log.info("H_avgs Shape: %s" % str(H_avgs.shape))
        #log.info("T_avgs Shape: %s" % str(T_avgs.shape))
        #log.info("T      Shape: %s" % str(     T.shape))

        best_k  = 0.0
        ind_k   = 0
    
        map_arguments = zip(
            repeat(H),
            repeat(T),
            repeat(self._tlen),
            repeat(H_avgs),
            repeat(T_avgs),
            range(0, self.K),
            repeat(self.D)
        )
        
        start = time.time()

        with Pool(self.num_threads) as p:
            results = p.starmap(parallel_compute_R, map_arguments)

            for i in range(0, self.K):
                R[i,:] = results[i]
        
        log.info("Finished in: %03fS" % (time.time()-start))

        best_k = R.max() 
        ind_k  = np.where(R==R.max())[0][0]

        return (ind_k,best_k,R)
    
    @property
    def num_threads(self):
        """
        Return the number of threads used to compute the corrolation
        coefficient for each byte.
        """
        return self._num_threads
    
    @num_threads.setter
    def num_threads(self, v):
        """
        Set the number of threads used to compute the corrolation
        coefficient for each byte.
        """
        self._num_threads = v

    @property
    def K(self):
        """Number of possible key guesses"""
        return self._k
    
    @property
    def D(self):
        """Number of traces"""
        return min(self._tnum, self.max_traces)
    
    @property
    def T(self):
        """Length of each trace"""
        return self._tlen
