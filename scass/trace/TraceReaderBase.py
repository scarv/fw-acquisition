
import numpy as np

class TraceReaderBase(object):
    """
    Base class for reading traces from disk.
    """

    def __init__(self, file_handle, dtype = None):
        """
        Create a new trace reader object
        """

        self._fh            = file_handle

        self._longest_trace = 0

        self.dtype          = dtype
        self.traces         = []
        self.aux_data       = []

        self._readHeader()


    def _readHeader(self):
        """
        Read any header information from the file.
        """

    def readTraces(self, n=None):
        """
        Read the next n traces from the file. If n is None, all traces
        are read. If n is greater than the number of traces in the file,
        read upto the end of the file.
        Returns the number of traces read due to this function call.
        """
        before = len(self.traces)
        
        self._readTraces(n)

        return len(self.traces) - before

    
    def _readTraces(self, n=None):
        """
        Internal read traces function. Responsible for actually reading
        and interpreting the trace file and adding the loaded
        traces to the internal self.traces list.
        """
        raise NotImplementedError("_readTraces not implemented")


    @property
    def traces_read(self):
        """Return number of traces read from disk"""
        return len(self.traces)

    @property
    def longest_trace(self):
        """Return the length of the longest read trace so far."""
        return self._longest_trace

