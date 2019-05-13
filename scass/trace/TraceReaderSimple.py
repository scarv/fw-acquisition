
import io

import numpy as np

from .TraceReaderBase import TraceReaderBase

class TraceReaderSimple(TraceReaderBase):
    """
    Companion class to TraceWriterSimple. Reads traces from files that
    class writes.
    """
    
    def _readHeader(self):
        
        header      = self._fh.read(10)

        dtypebytes  = header.rstrip(b"\x00")

        headerbytes = str(dtypebytes, encoding="ascii")
        
        fdtype = np.dtype(headerbytes)

        if(self.dtype == None):
            self.dtype == fdtype
        elif(self.dtype != fdtype):
            raise TypeError("Expected dtype %s, got %s" % (
                self.dtype, fdtype))


    def _readTraces(self, n = None):
        
        nread = 0

        while(n == None or nread < n):
            
            rbytes  = self._fh.read(4)
            abytes  = self._fh.read(4)

            if(len(rbytes) == 0):
                return # EOF, file empty.

            # Items in the trace
            tlen    = int.from_bytes(rbytes,"little")

            # Length of aux data in bytes
            alen    = int.from_bytes(abytes,"little")
            
            trace   = np.fromfile(self._fh, dtype=self.dtype,count=tlen)
            auxdata = None
            
            if(alen > 0):
                np.fromfile(self._fh, dtype=np.uint8,count=alen)

            self.traces.append(trace)
            self.aux_data.append(auxdata)

            self._longest_trace = max(len(trace), self._longest_trace)

            nread += 1
    
