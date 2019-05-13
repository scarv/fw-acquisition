
import secrets

from tqdm    import tqdm

from ..comms import Target
from ..trace import TraceWriterBase

def __no_progress_bar(x):
    return x

class TTestCapture(object):
    """
    A class which automates the capture process for TTest trace sets.
    
    Based on TVLA guidance found in:
    - https://www.rambus.com/wp-content/uploads/2015/08/TVLA-DTR-with-AES.pdf
    """


    def __init__(self, target, ts1, ts2, num_traces = 1000):
        """
        Create a new ttest capture class.
        
        Parameters:
        target - scass.comms.Target
            Class used to communicate with the target device

        ts1 - scass.trace.TraceWriterBase
            Trace set containing "fixed" data value.

        ts2 - scass.trace.TraceWriterBase
            Trace set containing "random" data values.

        num_traces : int
            The number of traces to capture in total.
        """

        assert(isinstance(target, Target))
        assert(isinstance(ts1, TraceWriterBase))
        assert(isinstance(ts2, TraceWriterBase))

        self.__progress_bar     = True
        self.__progress_bar_func= tqdm

        self.target         = target
        self.ts1            = ts1
        self.ts2            = ts2

        self.num_traces     = num_traces
        self.min_traces     = num_traces/2

        # Length of experiment data array on the target.
        self.target_data_len= None

        self.__fixed_value  = None


    def __update_target_fixed_data(self):
        """
        This function should be overriden by inheriting classes, and
        is responsible for updating the target data to the "fixed" value.

        Returns: The fixed data value as a byte string.
        """
        pass

    
    def __update_target_random_data(self):
        """
        This function should be overriden by inheriting classes, and
        is responsible for updating the target data to "random" values.

        Returns: The random data value as a byte string.
        """
        pass


    def __prepare(self):
        """
        Called once at the start of the data capture, used to gather
        information on the target.
        """

        # Get the length of the target experiment data array.
        self.target_data_len = target.doGetExperiementDataLength()
        self.__fixed_value   = secrets.token_bytes(self.target_data_len)


    def runTTest(self):
        """
        Runs the ttest data capture.
        """

        self.__prepare()

        for i in self.__progress_bar_func(range(0,self.num_traces)):

            pass

    # ------------------

    @property
    def progress_bar(self):
        return self.__progress_bar

    @progress_bar.setter
    def progress_bar(self,v):
        assert(isinstance(v,bool))
        self.__progress_bar = v
        if(v):
            self.__progress_bar_func = tqdm
        else:
            self.__progress_bar_func = __no_progress_bar

