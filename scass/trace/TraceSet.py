
import numpy as np

from .TraceReaderBase import TraceReaderBase

def ResampleLinear1D(original, targetLen):
    """
    Taken from stackoverflow...
    https://stackoverflow.com/questions/20322079/downsample-a-1d-numpy-array
    """
    original = np.array(original, dtype=np.float)
    index_arr = np.linspace(0, len(original)-1, num=targetLen, dtype=np.float)
    index_floor = np.array(index_arr, dtype=np.int) #Round down
    index_ceil = index_floor + 1
    index_rem = index_arr - index_floor #Remain

    val1 = original[index_floor]
    val2 = original[index_ceil % len(original)]
    interp = val1 * (1.0-index_rem) + val2 * index_rem
    assert(len(interp) == targetLen)
    return interp

class TraceSet(object):
    """
    A collection of traces which can be subjected to bulk processing,
    analysis and storage.
    """

    def __init__(self):
        """
        Create a new empty trace set.
        """
        
        # List of traces being analysed
        self.__traces   = []

        # Associated auxiliary data
        self.__aux_data = []


    def addTrace(self, trace, aux_data, trim_pad = False):
        """
        Add a new trace and associated data to the to the set.

        parameters:
        trace: np.ndarray
            The trace to add
        aux_data: np.ndarray
            Associated trace data. Can be None / zero length
        trim_pad: bool
            If true, zero pad or trim the length of the new trace
            to the same size as the zeroth trace currently in the set.
        """
        
        if(trim_pad and len(self.__traces) > 0):
            
            t0len = self.__traces[0].size

            if(trace.size > t0len):
                self.__traces.append(trace[0:t0len])

            elif(trace.size < t0len):
                ta = np.pad(trace,(0,t0len-trace.size),'constant',
                    constant_values=(0,0))
                self.__traces.append(ta)

            else:
                self.__traces.append(trace)


        else:
            self.__traces.append(trace)
        
        self.__aux_data.append(aux_data)

    def trimTraces(self, N):
        """
        Trim traces so that they are all N elements long, where N is less
        than the current length.
        """
        
        L = min(N,self.trace_length)

        for i in range(0, self.num_traces):

            self.__traces[i] = self.__traces[i][0:L]


    def tracesAs2dArray(self):
        """
        Returns a 2d ndarray object of all traces, where one row
        of the return value is one trace.
        Will fail if traces_are_uniform_length == False
        """
        tr = np.transpose(np.array(self.__traces))
        return tr


    def auxDataAs2dArray(self):
        """
        Returns a 2d ndarray object of all aux-data elements, where
        one row of the return value is one array of aux data.
        """
        return np.array(self.__aux_data)


    def averageTrace(self):
        """
        Return the average of all traces in the set.
        """
        return np.mean(
            self.tracesAs2dArray(),
            axis = 1)

    def standardDeviation(self):
        """
        Return the standard deviation over time across all traces.
        Returns an ndarray as long as self.trace_length, where each
        element I is the standard deviation over the I'th elements of
        all traces.
        """
        return np.std(
            self.tracesAs2dArray(),
            axis = 1)

    def loadFromTraceReader(self, reader, n = None):
        """
        Load traces from the supplied trace reader object into
        the set.
        """
        assert(isinstance(reader, TraceReaderBase))
        
        reader.readTraces(n)

        self.__traces   = reader.traces
        self.__aux_data = reader.aux_data


    def convolveTraces(self, weights):
        """
        For each trace in the set, apply the supplied `weights` convolution
        filter, where weights is "array like". Uses the numpy.convolve
        function.
        This operation is destructive. The original traces can only be
        recovered by re-loading them from somewhere.
        """

        for i,trace in enumerate(self.__traces):
            
            self.__traces[i] = np.convolve(trace, weights, 'same')

    def convolveTracesUniform(self, l):
        """
        Calls convolveTraces with an 'l' length convolution filter, where
        all elements in l are 1.
        """
        self.convolveTraces([1]*l)


    def subsampleTraces(self, factor):
        
        ntlen = int(self.trace_length / factor)
        
        for i in range(0,len(self.__traces)):

            newtrace = ResampleLinear1D(self.__traces[i], ntlen)
            self.__traces[i] = newtrace


    @property
    def traces_are_uniform_length(self):
        """Return true if all traces are the same length, otherwise False"""
        l0 = self.__traces[0].size
        for t in self.__traces[1:]:
            if(t.size != l0):
                return False
        return True

    @property
    def trace_length(self):
        """Return the length of the zeroth trace in the set"""
        return self.__traces[0].size
    
    @property
    def traces_and_aux_data(self):
        """Return a list of tuples of the form (trace, aux data)"""
        return zip(self.__traces, self.__aux_data)

    @property
    def num_traces(self):
        """Return the number of traces in the set"""
        return len(self.__traces)

    @property
    def traces(self):
        """Return a list of numpy.ndarray objects"""
        return self.__traces

    @property
    def aux_data(self):
        """Return a list of numpy.ndarray objects"""
        return self.__aux_data

