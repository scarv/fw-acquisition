
import numpy as np

from tqdm import tqdm

from ..trace.TraceSet import TraceSet

class CorrolationAnalysis(object):
    """
    A class for performing corrolation based analysis on sets of
    traces.
    """

    def __init__(self, traces):
        """
        Create a new CorrolationAnalysis object which will operate
        on the supplied traces.

        parameters:
        ----------
        traces - TraceSet
            The set of traces to work with
        """

        self.tmat = traces.tracesAs2dArray()
        self.amat = traces.auxDataAs2dArray()
        self.tlen, self.tnum = self.tmat.shape

    def computeH(self, model, max_k = 1):

        H = np.array(
            [model.getEstimate(self.amat[d,:],k) 
                for k in range(0,max_k)
                    for d in range(0,self.tnum)],
            dtype=np.float32,
            order='C'
        )

        return H
    
    def getCorrolation(self, H):
        """
        Take a single value/power estimate and turn it into an N length
        vector where N is the number of traces in tmat.
        Then compute the per-sample corrolation over the trace set, and
        return the 1*M corrolation array, where M is the length of the
        traces in the set.
        i = num traces = self.tnum - i = 0...(D-1)
        j = trace len  = self.tlen - k = 0...(K-1)
        """

        c_out = np.zeros(self.tlen,dtype=np.float32)
        
        #print("H Shape: %s" % str(H.shape))
        #print("T Shape: %s" % str(self.tmat.shape))

        col_H_avgs = np.mean(H        ,axis=0)
        col_T_avgs = np.mean(self.tmat,axis=1)

        #print("col_H_avgs Shape: %s" % str(col_H_avgs.shape))
        #print("col_T_avgs Shape: %s" % str(col_T_avgs.shape))
        #print("col_H_avgs      : %s" % str(col_H_avgs))

        i = 0
        for j in range(0,self.tlen):

            col_T           = self.tmat[j,:]
            col_T_norm      = col_T - col_T_avgs[j]
            col_T_norm_sq   = np.square(col_T_norm)

            col_H_norm      = H - col_H_avgs
            col_H_norm_sq   = np.square(col_H_norm)

            top             = np.sum(np.multiply(col_H_norm, col_T_norm))
            bottom          = np.sum(np.multiply(col_H_norm_sq, col_T_norm_sq))
            
            bottom          = np.sqrt(bottom)
        
            #print("col_T         Shape: %s" % str(col_T.shape))
            #print("col_T_norm    Shape: %s" % str(col_T_norm.shape))
            #print("col_T_norm_sq Shape: %s" % str(col_T_norm_sq.shape))
            #print("col_H_norm    Shape: %s" % str(col_H_norm.shape))
            #print("col_H_norm_sq Shape: %s" % str(col_H_norm_sq.shape))

            c_out[j]        = abs(top / bottom)

            #print("top / bottom       : %f / %f = %f" %(top,bottom,c_out[j]))

        return c_out

