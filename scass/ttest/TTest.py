
import numpy as np

from ..trace.TraceSet import TraceSet

class TTest(object):
    """
    Class for performing Welch's TTest on trace sets.
    """

    def __init__(self, ts_fixed, ts_random):
        """
        Create a new TTest object, perform the ttest, and produce
        useful outputs.

        paramters:
        ts_fixed - TraceSet
            The "fixed" value trace set
        ts_random: - TraceSet
            The "random" value trace set
        """

        assert(ts_fixed.num_traces > 0)
        assert(ts_random.num_traces > 0)

        self.ts_fixed   = ts_fixed
        self.ts_random  = ts_random

        self.__ttrace     = None
        
        self.__doWelchTTest()

    def __doWelchTTest(self):
        """
        Perform the ttest
        """

        avg_fixed = self.ts_fixed.averageTrace()
        avg_random= self.ts_random.averageTrace()

        avg_sum   = avg_fixed - avg_random

        std_fixed = np.square(self.ts_fixed.standardDeviation())
        div_fixed = np.divide(std_fixed, self.ts_fixed.num_traces)

        std_random= np.square(self.ts_random.standardDeviation())
        div_random= np.divide(std_random, self.ts_random.num_traces)

        denom = np.sqrt(div_fixed + div_random)

        self.__ttrace = avg_sum / denom
    
    @property
    def ttrace(self):
        return self.__ttrace

    @property
    def abs_ttrace(self):
        return np.abs(self.__ttrace)
