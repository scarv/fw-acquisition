
"""
This file contains tools for archiving sets of traces.
"""

import os
import sys
import numpy as np
import logging as log

from .SassTrace import *

class SassStorage:
    """
    A class for storing sets of traces, and then dumping them
    out to a file.
    """


    def __init__(self):
        """
        Create a new storage class for dumping traces into.
        """

        self.traces = []


    def __len__(self):
        return len(self.traces)


    def AddTrace(self, trace):
        """
        Add a new trace to the set
        """
        assert(type(trace) == SassTrace)
        self.traces.append(trace)


    def ClearTraces(self):
        """
        Scrub the collection of traces.
        """
        self.traces = []


    def DumpCSV(self, filepath):
        """
        Write out the collection of traces to the supplied filepath,
        overwriting any existing file of the same name.
        CSV Format
        """
        log.info("Dumping %d traces to %s" % (len(self.traces),filepath))

        with open(filepath,"w") as fh:

            tw = "Key,Message,Data\n"

            for t in self.traces:
                tw += str(t)+"\n"

            fh.write(tw)

    def DumpTRS(self,filepath):
        """
        Write out the collection of traces to the supplied filepath,
        overwriting any existing file of the same name.
        TRS Format
        """
        log.info("Dumping %d traces to %s" % (len(self.traces),filepath))

        with open(filepath,"wb") as fh:
            pass
