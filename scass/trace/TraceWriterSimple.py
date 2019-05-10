
from .TraceWriterBase import TraceWriterBase

class TraceWriterSimple(TraceWriterBase):
    """
    A super simple trace writer class which just dumps out numpy
    arrays as bytes, prefixed by their length.
    """


    def _writeHeader(self, trace):
        """
        Write any header information needed by the file.
        Must be done *before* any traces are written.
        Called automatically by the writeTrace function, once and only
        once.
        """
        
        if(trace.dtype != self.dtype):
            raise ValueError("Expected trace data type %s, but got %s" %(
                self.dtype.name, trace.dtype))

        headerbytes = bytes(self.dtype.str, encoding="ascii")

        hlen = len(headerbytes)
        assert(len(headerbytes) <= 10)

        self._fh.write(headerbytes)

        while(hlen < 10):
            self._fh.write(b"\x00")
            hlen += 1
        

    def _writeTrace(self, trace):
        """
        Write the numpy array out as bytes, prefixed by it's length
        as a 32-bit integer.
        The length prefix is 4 bytes long, stored in little endian
        byte order.
        """
        
        if(trace.dtype != self.dtype):
            raise ValueError("Expected trace data type %s, but got %s" %(
                self.dtype.name, trace.dtype))

        alen    = trace.size
        blen    = alen.to_bytes(4,byteorder="little")
        
        tbytes  = trace.tobytes(order='C')

        self._fh.write(blen)
        self._fh.write(tbytes)

