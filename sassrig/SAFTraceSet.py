
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

class SAFTraceSet:
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
        
        self._traces            = None
        self._plaintexts        = None

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
    
    @coding_type.setter
    def coding_type(self,nv):
        """ Set the trace encoding type """
        self._coding_type = nv

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

    def Allocate(self, num_traces, trace_len, plaintext_len):
        """
        Create the empty matricies which will hold the trace and message
        data.

        Creates the matricies and sets the number of traces, plaintext length
        and trace length.
        """
        
        self._num_traces    = num_traces
        self._trace_len     = trace_len
        self._plaintext_len = plaintext_len

        t_shape = (self._num_traces, self._trace_len)
        m_shape = (self._num_traces, self._plaintext_len)

        self._traces     = np.empty(t_shape, dtype=np.float)
        self._plaintexts = np.empty(m_shape, dtype=np.int8)


    def AddTrace(self, plaintext, trace):
        """
        Add a new trace to the set
        """
        
        if(self._tcounter > self._num_traces):
            raise Exception("Allocated space for %d traces but you are trying to add more than that." % self._num_traces)


        begin   = self._tcounter

        assert(len(trace)     == self._trace_len    ), "%d != %d" %(len(trace)     , self._trace_len    )
        assert(len(plaintext) == self._plaintext_len), "%d != %d" %(len(plaintext) , self._plaintext_len)

        self._traces[begin] =  trace

        self._plaintexts[begin] = plaintext

        self._tcounter += 1


    def DumpTRS(self,filepath):
        """
        Write out the collection of traces to the supplied filepath,
        overwriting any existing file of the same name.
        TRS Format
        """

        num_traces = len(self.traces)
        len_traces = self.trace_len

        with open(filepath,"wb") as fh:
            
            fh.write(b"\x41") # Number of traces
            fh.write(num_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x42") # Samples per trace
            fh.write(len_traces.to_bytes(4,byteorder="little"))

            fh.write(b"\x43") # Sample coding type (float, 4 bytes)
            fh.write(SAMPLE_ENCODING_F4)

            fh.write(b"\x44") # Length of data associated with each trace
            fh.write(self.plaintext_len.to_bytes(2,byteorder="little"))
            
            fh.write(b"\x47") # Trace description
            ta = bytes(self.trace_description,encoding="ascii")
            fh.write(b"\x84") # Next 4 bytes give length of description
            fh.write(len(ta).to_bytes(4,byteorder="little"))
            fh.write(ta)

            fh.write(b"\x5f") # Trace block marker.
            
            towrite = np.concatenate((self._plaintexts,self._traces))
            towrite.tofile(fh)


    def LoadTRS(filepath, infoOnly = False):
        """
        Load a trs file from disk and return a new SAFTraceSet object

        :param str filepath: The path to the TRS file to load.
        :param bool infoOnly: If true, only the header information will be
            loaded. If False, the trace set data will be loaded as well.
        :rtype: SAFTraceSet
        """

        tr = SAFTraceSet()

        with open(filepath, "rb") as fh:

            ctrlcode            = fh.read(1)

            while(ctrlcode != b"\x5f"):

                log.debug("Control code: %s" % ctrlcode.hex())
                
                if(ctrlcode == b"\x41"):
                    # Number of traces
                    tr.num_traces = int.from_bytes(fh.read(4),"little")
                    
                elif(ctrlcode == b"\x42"):
                    # Samples per trace
                    tr.trace_length= int.from_bytes(fh.read(4),"little")

                elif(ctrlcode == b"\x43"):
                    # Sample coding type (float, 4 bytes each)
                    tr.coding_type = fh.read(1)

                    if(tr.coding_type != SAMPLE_ENCODING_F4):
                        raise Exception("Unsupported sample encoding: %s" % (
                            tr.coding_type))

                elif(ctrlcode == b"\x44"):
                    # Length of data (msg/cipher text) associated with a trace
                    tr.plaintext_len = int.from_bytes(fh.read(2),"little")
            
                elif(ctrlcode == b"\x47"):
                    # Trace description
                    lenb = int.from_bytes(fh.read(1),"little")
                    if(not lenb & 0x80):
                        tr.trace_description = fh.read(lenb).decode("ascii")
                    else:
                        lenb = int.from_bytes(fh.read(lenb&0x7F),"little")
                        tr.trace_description = fh.read(lenb).decode("ascii")

                else:
                    raise Exception("Unknown byte marker in TRS file: %x"%(
                        ctrlcode))

                ctrlcode = fh.read(1)

            # We have finished reading the header, now we just read the
            # rest of the data and traces.

            if(infoOnly):
                # We only want to load the headers.
                return tr

            pb = tqdm(range(0,tr.num_traces))
            pb.set_description("Loading Traces")

            tr.Allocate(tr.num_traces, tr.trace_length, tr.plaintext_length)

            message     = np.empty((tr.plaintext_length,),dtype=np.int8)
            tracedata   = np.empty((tr.trace_length    ,),dtype=np.float)

            for i in pb:
                
                message = np.fromfile(fh,count=tr.plaintext_length, dtype=np.int8)
                tracedata = np.fromfile(fh,count=tr.trace_length,dtype=np.float32)
                tr.AddTrace(message, tracedata)

        return tr

