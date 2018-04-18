
"""
This file contains tools for archiving sets of traces.
"""

import os
import sys
import struct
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

        self.traces    = []
        self.trace_len = None

    def __len__(self):
        return len(self.traces)


    def AddTrace(self, trace):
        """
        Add a new trace to the set
        """
        assert(type(trace) == SassTrace)
        self.traces.append(trace)
        if(self.trace_len == None):
            self.trace_len = len(trace)
        elif(self.trace_len != len(trace)):
            log.error("New trace length: %d, existing trace length: %d" %
                (len(trace),self.trace_len))
            log.error("Multiple trace lengths not supproted by trs files")


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

        num_traces = len(self.traces)
        len_traces = self.trace_len

        with open(filepath,"wb") as fh:
            
            fh.write(b"\x41") # Number of traces
            fh.write(num_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x42") # Samples per trace
            fh.write(len_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x43") # Sample coding type (float, 4 bytes)
            fh.write(b"\x14")

            fh.write(b"\x5f") # Trace block marker.

            # Write out all the trace data.
            for t in self.traces:
                buf = struct.pack("%sf" % len(t.data), *t.data)
                fh.write(buf)

