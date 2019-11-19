
import numpy as np

from ..trace.TraceSet import TraceSet

class TTest(object):
    """
    Class for performing Welch's TTest on trace sets.
    """

    def __init__(self, ts_fixed, ts_random, second_order=False):
        """
        Create a new TTest object, perform the ttest, and produce
        useful outputs.

        paramters:
        ts_fixed - np.ndarray
            The "fixed" value trace set
        ts_random: - np.ndarrau
            The "random" value trace set
        second_order - bool
            Perform a "second order ttest where the average traces
            are squared.
        """

        self.ts_fixed   = ts_fixed
        self.ts_random  = ts_random
        self.second_order = second_order

        self.__ttrace     = None
        
        self.__doWelchTTest()

    def __doWelchTTest(self):
        """
        Perform the ttest
        """

        avg_fixed = np.mean(self.ts_fixed , axis=0)
        avg_random= np.mean(self.ts_random, axis=0)

        if(self.second_order):
            avg_fixed = np.square(avg_fixed )
            avg_random= np.square(avg_random)

        avg_sum   = avg_fixed - avg_random

        std_fixed = np.square(np.std(self.ts_fixed, axis=0))
        div_fixed = np.divide(std_fixed, self.ts_fixed.shape[0])

        std_random= np.square(np.std(self.ts_random, axis=0))
        div_random= np.divide(std_random, self.ts_random.shape[0])

        denom = np.sqrt(div_fixed + div_random)

        self.__ttrace = avg_sum / denom
    
    @property
    def ttrace(self):
        return self.__ttrace

    @property
    def abs_ttrace(self):
        return np.abs(self.__ttrace)
