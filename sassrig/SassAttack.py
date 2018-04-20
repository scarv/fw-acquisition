
"""
This file is used to attack traces we have captured using the flow
"""


import os
import sys
import logging as log

from multiprocessing import Pool

import numpy as np
import matplotlib.pyplot as plt
from progress.bar import ShadyBar as progressbar

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
        
        pb = progressbar("Isolating traces...")
        for trace in pb.iter(self.storage.traces):
            trace.data = trace.data[self.isolate_start:self.isolate_end]
            self.storage.trace_len = len(trace.data)


    def getTracePartition(self, trace, candidate, bytei):
        """
        Returns which partition set the supplied trace should be put into.
        For a given candidate byte, and the bytei'th byte of the data 
        associated with the supplied trace, work out the partition the
        trace belongs too.
        """

        assert(type(trace)      == SassTrace)
        assert(type(candidate)  == int)
        assert(candidate >= 0 and candidate <= 255)
        assert(type(bytei)      == int)
        assert(bytei < len(trace.message))


        message_byte = trace.message[bytei]

        candidate_xor_msgbyte = message_byte ^ candidate
        
        # Partition based on least significant bit of candidate XOR data byte
        partition = candidate_xor_msgbyte & (0x1)

        return partition


    def createSetAverage(self, traceset):
        """
        Return a numpy array which represents the pointwise average of all
        traces in the supplied set.
        """
        
        data = np.array([t.data for t in traceset])

        toreturn = np.average(data,axis=0)

        assert(len(toreturn) == self.storage.trace_len)

        return toreturn



    def createPartitionSets(self, candidate, bytei):
        """
        For a particular candidate and byte index, compute the two partitioned
        trace sets, and the average traces of those two sets, returning
        them as a tuple.
        """
        
        # Split all of the traces into two sets based on the
        # partition function
        for trace in self.storage.traces:
            partition = self.getTracePartition(trace,candidate, bytei)

            if(partition):
                self.partition_sets_1[candidate].append(trace)
            else:
                self.partition_sets_0[candidate].append(trace)



    def plotCandidateSets(self,candidate):
        """
        Plot the average and difference sets for a candidate
        """

        plt.figure(2)

        plt.subplot(311)
        plt.plot(self.average_set_0[candidate], linewidth=0.1)

        plt.subplot(312)
        plt.plot(self.average_set_1[candidate], linewidth=0.1)
        
        plt.subplot(313)
        plt.plot(self.difference_sets[candidate], linewidth=0.1)

        plt.suptitle("Candidate = %s" % hex(candidate))

        plt.show()
        plt.draw()
        plt.pause(0.001)

        

    def getCandidateForKeyByte(self, keybyte):
        best_candidate_value = -1
        best_candidate_corr  = 0.0
        candidates = range(0,255)

        log.info("Partitioning Traces...")
        
        for c in progressbar("Partitioning...").iter(candidates):

            self.partition_sets_0[c] = []
            self.partition_sets_1[c] = []

            self.createPartitionSets(c, keybyte)
        
        log.info("Averaging Traces...")
        
        for c in progressbar("Averaging...   ").iter(candidates):
            set0 = self.partition_sets_0[c]
            set1 = self.partition_sets_1[c]
            avg0 = self.createSetAverage(set0)
            avg1 = self.createSetAverage(set1)
            self.average_set_0[c]   = avg0
            self.average_set_1[c]   = avg1
            self.difference_sets[c] = avg0 - avg1

        log.info("Searching for best candidate...")

        for c in progressbar("Finding best candidate...").iter(candidates):

            val = np.max(self.difference_sets[c]) - np.min(self.difference_sets[c])

            if(val > best_candidate_corr):
                best_candidate_corr  = val
                best_candidate_value = c

                log.info("Best candidate for byte %d is %s" % 
                    (keybyte, hex(best_candidate_value)))
        return best_candidate_value



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
        for i in range(0, 1):

            self.partition_sets_0 = {}
            self.partition_sets_1 = {}

            self.average_set_0    = {}
            self.average_set_1    = {}

            self.difference_sets  = {}

            keybytes[i] = self.getCandidateForKeyByte(i)
            self.plotCandidateSets(keybytes[i])

        log.info("Final key guess: %s" % keybytes)
        plt.ioff()
        plt.show()


