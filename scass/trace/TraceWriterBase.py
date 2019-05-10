
import os
import sys

import numpy as np

class TraceWriterBase(object):
    """
    Base class for writing out trace data to a file.
    """

    def __init__(self, file_handle, dtype=np.int32):
        """
        Create a new trace writer object.
        """

        self._fh = file_handle

        self._write_through  = True
        self.dtype           = dtype

        self._traces_written = 0
        self._longest_trace  = 0

        self._pending_traces = [] # traces not yet flushed to disk
        self.__header_written= False


    def writeTraces(self, traces):
        """Takes an iterable of traces and calls writeTrace on each one"""
        for t in traces:
            self.writeTrace(t)


    def writeTrace(self, trace):
        """
        Write a trace to disk. The trace will be written immediately
        or held in memory depending on self.write_through
        """
        assert(isinstance(trace, np.ndarray))

        if(not self.__header_written):
            self._writeHeader(trace)
            self.__header_written = True

        if(self._write_through):

            self._writeTrace(trace)
            self._traces_written += 1

        else:

            self._pending_traces.append(trace)

        self._longest_trace   = max(self._longest_trace, len(trace))


    def flushTraces(self):
        """
        Write all cached pending traces to disk.
        """
        while(len(self._pending_traces) > 0):
            
            t = self._pending_traces.pop()

            self._writeTrace(t)
            self._traces_written += 1


    def _writeHeader(self, trace):
        """
        Write any header information needed by the file.
        Must be done *before* any traces are written.
        Called automatically by the writeTrace function, once and only
        once.
        """

    def _writeTrace(self, trace):
        """
        Underlying function inheriting classes should overwrite to
        actually implement dumping the supplied trace to a file.
        """
        raise NotImplementedError("__writetrace not implemented")

    @property
    def unwritten_traces(self):
        """The number of cached traces not yet written to disk"""
        return len(self._pending_traces)

    @property
    def traces_written(self):
        """Return number of traces written out so far"""
        return self._traces_written

    @property
    def longest_trace(self):
        """Return the length of the longest written trace so far."""
        return self._longest_trace

    @property
    def write_through(self):
        """
        If true, each new trace is automatically writen to disk
        immediately after being added.
        If False, all traces are written to file after the flush()
        function is called.
        """
        return self._writethrough

    @write_through.setter
    def write_through(self, v):
        assert(isinstance(v,bool))
        self._write_through = v
