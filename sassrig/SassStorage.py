
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

from .SassTrace     import *
from .SassStorage   import *

SAMPLE_ENCODING_F4 = b"\x14"

class SassStorage:
    """
    A class for storing sets of traces, and then dumping them
    out to a file.
    """


    def __init__(self, trs_file = None, info_only=False):
        """
        Load back a trs file from disk as a set of traces.
        """

        self.traces    = []
        self.trace_len = None
        self.plaintext_len = 16 # bytes
        self.trace_description = "No Description"
        self.info_only = info_only
        
        if(trs_file != None):
            self.LoadTRS(trs_file)


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

            fh.write("Key,Message,Data\n")

            pb = tqdm(self.traces)
            pb.set_description("Write CSV")

            for t in pb:
                fh.write(str(t)+"\n")


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
            fh.write(SAMPLE_ENCODING_F4)

            fh.write(b"\x44") # Length of data associated with each trace
            fh.write(self.plaintext_len.to_bytes(2,byteorder="little"))
            
            fh.write(b"\x47") # Trace description
            ta = bytes(self.trace_description,encoding="ascii")
            fh.write(b"\x84") # Next 4 bytes give length of description
            fh.write(len(ta).to_bytes(4,byteorder="little"))
            fh.write(ta)

            fh.write(b"\x5f") # Trace block marker.
            
            pb = tqdm(self.traces)
            pb.set_description("Write TRS")

            # Write out all the trace data.
            for t in pb:
                # Write the message associated with the trace
                fh.write(t.message)

                # Write the trace data.
                t.data.tofile(fh)


    def LoadTRS(self, filepath):
        """
        Load a trs file from disk.
        """

        with open(filepath, "rb") as fh:

            ctrlcode            = fh.read(1)
            self.numtraces           = None
            self.samples_per_trace   = None
            self.data_per_trace      = None
            self.coding_type         = None

            while(ctrlcode != b"\x5f"):

                log.debug("Control code: %s" % ctrlcode.hex())
                
                if(ctrlcode == b"\x41"):
                    # Number of traces
                    self.num_traces = int.from_bytes(fh.read(4),"little")
                    log.info("Number of traces: %d" % self.num_traces)
                    
                elif(ctrlcode == b"\x42"):
                    # Samples per trace
                    self.samples_per_trace = int.from_bytes(fh.read(4),"little")
                    self.trace_len = self.samples_per_trace
                    log.info("Samples per trace: %d" % self.samples_per_trace)

                elif(ctrlcode == b"\x43"):
                    # Sample coding type (float, 4 bytes each)
                    self.coding_type = fh.read(1)

                    if(self.coding_type != SAMPLE_ENCODING_F4):
                        log.error("Unsupported sample encoding: %s" % self.coding_type)
                        return
                    else:
                        log.info("Coding Type: float-4byte.")

                elif(ctrlcode == b"\x44"):
                    # Length of data (msg/cipher text) associated with a trace
                    self.data_per_trace = int.from_bytes(fh.read(2),"little")
                    log.info("Data bytes per trace: %d" % self.data_per_trace)
            
                elif(ctrlcode == b"\x47"):
                    # Trace description
                    lenb = int.from_bytes(fh.read(1),"little")
                    if(not lenb & 0x80):
                        self.trace_description = fh.read(lenb).decode("ascii")
                    else:
                        lenb = int.from_bytes(fh.read(lenb&0x7F),"little")
                        self.trace_description = fh.read(lenb).decode("ascii")

                else:
                    log.error("Unknown byte marker: %s"%ctrlcode)
                    return

                ctrlcode = fh.read(1)

            # We have finished reading the header, now we just read the
            # rest of the data and traces.

            if(self.info_only):
                # We only want to load the headers.
                return

            pb = tqdm(range(0,self.num_traces))
            pb.set_description("Loading Traces")

            for i in pb:
                
                message   = fh.read(self.data_per_trace)
                tracedata = array.array("f")
                tracedata.fromfile(fh, self.samples_per_trace)

                toadd = SassTrace(tracedata, message = message)
                self.AddTrace(toadd)

