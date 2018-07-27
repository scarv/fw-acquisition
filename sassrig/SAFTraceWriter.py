
"""
This file contains tools for archiving sets of traces.
"""

import os
import sys
import array
import struct
import numpy as np
import logging as log

from tqdm import tqdm

SAMPLE_ENCODING_F4 = b"\x14"

class SAFTraceWriter:
    """
    A class for storing sets of traces, and then dumping them
    out to a file.
    """


    def __init__(self):
        """
        Load back a trs file from disk as a set of traces.
        """

        self._tcounter          = 0
        
        self._num_traces        = 0
        self._trace_len         = None
        self._plaintext_len     = 16 # bytes
        self._trace_description = "No Description"
        self._coding_type       = SAMPLE_ENCODING_F4
        
        self._traces     = []
        self._plaintexts = []

    @property
    def traces(self):
        return self._traces

    @property
    def plaintexts(self):
        return self._plaintexts
    
    @property
    def trace_description(self):
        """ Get the description of this set """
        return self._trace_description
    
    @trace_description.setter
    def trace_description(self,nv):
        """ Set the description of this set """
        self._trace_description = nv
    
    @property
    def num_traces(self):
        """ Get the number of traces in this set """
        return self._num_traces
    
    @num_traces.setter
    def num_traces(self,nv):
        """ Set the number of traces in this set """
        self._num_traces = nv
    
    @property
    def coding_type(self):
        """ Get the trace encoding type """
        return self._coding_type

    @property
    def trace_length(self):
        """ Get the length of traces in this set """
        return self._trace_len

    @trace_length.setter
    def trace_length(self, nv):
        """ Set the length of traces in this set """
        self._trace_len = nv

    @property
    def plaintext_length(self):
        """ Get the length of plaintexts in this set """
        return self._plaintext_len

    @plaintext_length.setter
    def plaintext_length(self, nv):
        """ Set the length of plaintexts in this set """
        self._plaintext_len= nv

    def __len__(self):
        """
        Return the number of traces in the set.

        :rtype: int
        """
        return len(self.traces)


    def AddTrace(self, plaintext, trace):
        """
        Add a new trace to the set
        """
        self._trace_len = len(trace)
        self._traces.append(np.array(trace))
        self._plaintexts.append(np.array(plaintext))
        self.num_traces = len(self._traces)


    def DumpTRS(self,filepath):
        """
        Write out the collection of traces to the supplied filepath,
        overwriting any existing file of the same name.
        TRS Format
        """

        num_traces = len(self.traces)
        len_traces = self.trace_length

        with open(filepath,"wb") as fh:
            
            fh.write(b"\x41") # Number of traces
            fh.write(num_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x42") # Samples per trace
            fh.write(len_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x43") # Sample coding type (float, 4 bytes)
            fh.write(SAMPLE_ENCODING_F4)

            fh.write(b"\x44") # Length of data associated with each trace
            fh.write(self._plaintext_len.to_bytes(2,byteorder="little"))
            
            fh.write(b"\x47") # Trace description
            ta = bytes(self._trace_description,encoding="ascii")
            fh.write(b"\x84") # Next 4 bytes give length of description
            fh.write(len(ta).to_bytes(4,byteorder="little"))
            fh.write(ta)

            fh.write(b"\x5f") # Trace block marker.
            
            for i in range(0, self.num_traces):
                self._plaintexts[i].tofile(fh)
                self._traces[i].tofile(fh)
