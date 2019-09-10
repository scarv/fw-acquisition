
import numpy as np

from ..trace.TraceSet import TraceSet

class TTestIncremental(object):
    """
    Class for performing Welch's TTest on trace sets as they are
    captured.
    """

    def __init__(self, second_order=False):
        """
        Create a new TTestIncremental object
        paramters:
        second_order - bool
            Perform a "second order ttest where the average traces
            are squared.
        """

        self.avg_fixed_trace    = None
        self.avg_random_trace   = None

        self._ttrace           = None
        self._t_over_time      = []
        self._n_over_time      = []

        self._fixed_traces     = 0
        self._random_traces    = 0

    def addFixedTrace(self, t):
        """
        Add a new fixed-value trace to the class and update the
        current t-static trace over time.
        """
        if(self.avg_fixed_trace == None):
            self.avg_fixed_trace = t
        else:
            self.avg_fixed_trace = (self.avg_fixed_trace + t) / 2.0
        self._fixed_traces += 1

        if(self._fixed_traces > 0 and self._random_traces > 0):
            self.__update_ttrace()

    def addFixedTrace(self, t):
        """
        Add a new random-value trace to the class and update the
        current t-static trace over time.
        """
        if(self.avg_random_trace == None):
            self.avg_random_trace = t
        else:
            self.avg_random_trace = (self.avg_random_trace + t) / 2.0
        self._random_traces += 1

        if(self._fixed_traces > 0 and self._random_traces > 0):
            self.__update_ttrace()

    def __update_ttrace(self):
        """
        Perform the ttest and update the t-statistic trace.
        """

        avg_fixed  = self.avg_fixed_trace 
        avg_random = self.avg_random_trace

        if(self.second_order):
            avg_fixed  = np.square(avg_fixed )
            avg_random = np.square(avg_random)

        avg_sum   = avg_fixed - avg_random

        std_fixed = np.square(self.ts_fixed.standardDeviation())
        div_fixed = np.divide(std_fixed, self.ts_fixed.num_traces)

        std_random= np.square(self.ts_random.standardDeviation())
        div_random= np.divide(std_random, self.ts_random.num_traces)

        denom = np.sqrt(div_fixed + div_random)

        self._ttrace = avg_sum / denom

        max_t = np.max(self.abs_ttrace)

        self._n_over_time.append(self._fixed_traces + self._random_traces)
        self._t_over_time.append(max_t)

    
    @property
    def t_over_time(self):
        """Return T-Statistic over time"""
        return self._t_over_time
    
    @property
    def n_over_time(self):
        """Return number of traces over time"""
        return self._n_over_time
    
    @property
    def ttrace(self):
        return self._ttrace

    @property
    def abs_ttrace(self):
        return np.abs(self._ttrace)

