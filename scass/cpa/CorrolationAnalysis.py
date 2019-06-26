
import logging as log

import numpy as np

from tqdm import tqdm

from ..trace.TraceSet import TraceSet

from .AES import sbox as aes_sbox

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

        # split key and message into two different chunks
        self.keymat = self.amat[:, 0:keyBytes]
        self.msgmat = self.amat[:,keyBytes:keyBytes+messageBytes]

        self.type_V = np.uint8
        self.type_H = np.uint8

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

    def computeV(self, msgbyte = 1):
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
                V[i,j] = self._computeV(msgb,j,V,i,j)

        return V

    def hw(self, x):
        """Return hamming weight of x"""
        c = 0
        while x:
            c  += 1
            x &= x-1
        return c

    def hd(self, x, y):
        """Return hamming distance between x and y"""
        return self.hw(x ^ y)

    def computeH(self, V):
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
        T_avgs  = np.mean(T, axis=1)

        #log.info("H_avgs Shape: %s" % str(H_avgs.shape))
        #log.info("T_avgs Shape: %s" % str(T_avgs.shape))

        best_k  = 0.0
        ind_k   = 0

        for i in tqdm(range(0,self.K)):

            H_avg   = H_avgs[i]
            H_col   = H[:,i]
            H_col_d = H_col - H_avg
            H_col_sq_sum = np.dot(H_col_d,H_col_d)
        
            #log.info("H_col    Shape: %s" % str(H_col   .shape))
            #log.info("H_col_d  Shape: %s" % str(H_col_d .shape))

            for j in range(0,self.T):

                T_avg   = T_avgs[i]
                T_col   = T[:self.D,j]
                T_col_d = T_col - T_avg
                T_col_sq_sum = np.dot(T_col_d, T_col_d)
            
                #log.info("T_col    Shape: %s" % str(T_col   .shape))
                #log.info("T_col_d  Shape: %s" % str(T_col_d .shape))

                top = np.dot(H_col_d, T_col_d)

                bot = np.sqrt(H_col_sq_sum * T_col_sq_sum)

                R[i,j] = np.abs(top/bot)

                if R[i,j]>best_k:
                    best_k = R[i,j]
                    ind_k  = i

        return (ind_k,R)
    

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
