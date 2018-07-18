
import random

import numpy as np

import matplotlib.pyplot as plt

from tqdm import tqdm

from .SassTrace      import SassTrace
from .SassStorage    import SassStorage
from .SassEncryption import SassEncryption

class SAFTTestEvaluation(object):
    """
    Responsible for performing a Welch T-test on two sets of traces.
    """


    def __init__(self, set1_filepath, set2_filepath):
        """
        Create a new TTest Capture object.
        
        :param str set1_filepath: File path to the first set of traces, where
            every trace corresponds to the same key and message
        :param str set2_filepath: File path to the second set of traces,
            where the same key is used for set1, but the messages are
            uniformly random.
        """

        self.set1_path = set1_filepath
        self.set2_path = set2_filepath

        self.set1_size = None
        self.set2_size = None
        
        # Average of all traces per set
        self.set1_avg  = None
        self.set2_avg  = None
        
        # Sample standard deviation over time of each set
        self.set1_ssd  = None
        self.set2_ssd  = None

        # The final t-statistic trace
        self.ttrace    = None

        # Confidence threshold
        self.confidence= 4.5


    def __compute_avg_ssd(self, path):
        """
        Compute the average trace and standard deviation for a single
        trace set, given the file path of the .trs file. This function
        will load the entire database, do its work and then unload the
        database.

        :param str path: The file path of the trace set to operate on.
        :rtype: tuple
        :return: A tuple of the form 
            (set size, average trace, standard deviation)
        """

        ts      = SassStorage(trs_file = path)
        
        # Matrix of traces
        trace_m = np.array(
            [t.data for t in ts.traces]
        )

        t_len = len(ts)

        del ts

        t_avg = np.average(trace_m,  axis=0)
        t_ssd = np.std(trace_m, axis=0)

        return (t_len, t_avg, t_ssd)


    def Evaluate(self):
        """
        Run the T-Test
        """

        self.set1_size, self.set1_avg, self.set1_ssd = \
            self.__compute_avg_ssd(self.set1_path)

        self.set2_size, self.set2_avg, self.set2_ssd = \
            self.__compute_avg_ssd(self.set2_path)

        avg_diff    = self.set1_avg - self.set2_avg

        set1_ssd_sqd = np.square(self.set1_ssd) / float(self.set1_size)
        set2_ssd_sqd = np.square(self.set2_ssd) / float(self.set2_size)

        ssd_sqd_sum  = set1_ssd_sqd + set2_ssd_sqd
        ssd_sqrt     = np.sqrt(ssd_sqd_sum)

        self.ttrace  = avg_diff / ssd_sqrt

        tr = (np.max(self.ttrace) < self.confidence)     and \
             (np.min(self.ttrace) > (0.0-self.confidence))
        
        return tr


    def make_graph(self):
        """
        Creates and returns a matplotlib figure showing the plots
        of each part of the ttrace calculation.
        """
        fig = plt.figure()

        plt.subplot(4,1,1)
        plt.plot(self.set1_avg, linewidth=0.25)
        plt.ylabel("Power")
        plt.xlabel("Time")
        plt.title("Set 1 Average Trace",fontsize=11)

        plt.subplot(4,1,2)
        plt.plot(self.set2_avg, linewidth=0.25)
        plt.ylabel("Power")
        plt.xlabel("Time")
        plt.title("Set 2 Average Trace",fontsize=11)

        plt.subplot(4,1,3)
        plt.plot(self.set1_avg-self.set2_avg, linewidth=0.25)
        plt.ylabel("Power")
        plt.xlabel("Time")
        plt.title("Difference of average traces: set1 - set2",fontsize=11)

        plt.subplot(4,1,4)
        plt.plot(self.ttrace, linewidth=0.25)
        plt.plot([ self.confidence]*len(self.ttrace), linewidth=0.25,
            color="red")
        plt.plot([-self.confidence]*len(self.ttrace), linewidth=0.25,
            color="red")
        plt.ylabel("Leakage")
        plt.xlabel("Time")
        plt.title("T-Statistic Trace",fontsize=11)

        plt.tight_layout(pad=0)

        return fig


        
