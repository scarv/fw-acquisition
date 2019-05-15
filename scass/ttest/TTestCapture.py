
import random
import secrets

import numpy as np

from tqdm    import tqdm

from ..comms import Target
from ..scope.Scope import Scope
from ..scope.ScopeChannel import ScopeChannel
from ..trace import TraceWriterBase

def __no_progress_bar(x):
    return x

class TTestCapture(object):
    """
    A class which automates the capture process for TTest trace sets.
    
    Based on TVLA guidance found in:
    - https://www.rambus.com/wp-content/uploads/2015/08/TVLA-DTR-with-AES.pdf
    """


    def __init__(self, 
                 target,
                 scope,
                 trigger_channel,
                 signal_channel,
                 ts_fixed, ts_rand,
                 num_traces = 1000,
                 num_samples= 1000):
        """
        Create a new ttest capture class.
        
        Parameters:
        target - scass.comms.Target
            Class used to communicate with the target device

        scope - scass.scope.Sope
            Oscilliscope control object.

        trigger_channel - scass.scope.ScopeChannel
            The scope channel setup as the trigger.

        signal_channel - scass.scope.ScopeChannel
            The scope channel setup as the signal to capture.

        ts_fixed - scass.trace.TraceWriterBase
            Trace set containing "fixed" data value.

        ts_rand - scass.trace.TraceWriterBase
            Trace set containing "random" data values.

        num_traces : int
            The number of traces to capture in total.

        num_samples: int
            The numer of samples to capture per trace.
        """

        assert(isinstance(target, Target))
        assert(isinstance(scope, Scope))
        assert(isinstance(trigger_channel, ScopeChannel))
        assert(isinstance(signal_channel, ScopeChannel))
        assert(isinstance(ts_fixed, TraceWriterBase))
        assert(isinstance(ts_rand , TraceWriterBase))

        self.__progress_bar     = True
        self.__progress_bar_func= tqdm

        self.target         = target
        self.scope          = scope
        self.trigger_channel= trigger_channel
        self.signal_channel = signal_channel
        self.ts_fixed       = ts_fixed
        self.ts_rand        = ts_rand

        self.num_samples    = num_samples
        self.num_traces     = num_traces
        self.min_traces     = num_traces/2

        # Store test input data with each trace?
        self.store_input_with_trace = False

        # Length of experiment data array on the target.
        self.input_data_len = None


    def update_target_fixed_data(self):
        """
        This function should be overriden by inheriting classes, and
        is responsible for updating the target data to the "fixed" value.

        Returns: The fixed data value as a byte string.
        """
        return secrets.token_bytes(self.input_data_len)

    
    def update_target_random_data(self):
        """
        This function should be overriden by inheriting classes, and
        is responsible for updating the target data to "random" values.

        Returns: The random data value as a byte string.
        """
        return secrets.token_bytes(self.input_data_len)


    def __prepare(self):
        """
        Called once at the start of the data capture, used to gather
        information on the target.
        - Gets length of input data
        - Runs the target.doInitExperiment() function
        - Generates a *random* fixed value to use.
        """

        # Get the length of the target experiment data array.
        self.input_data_len = self.target.doGetInputDataLength()
        self.__fixed_value  = self.update_target_fixed_data()

        assert(len(self.__fixed_value) == self.input_data_len)
        
        self.target.doInitExperiment()


    def runTTest(self):
        """
        Runs the ttest data capture.
        """

        self.__prepare()

        for i in self.__progress_bar_func(range(0,self.num_traces)):
            
            fixed_data = random.choice([True,False])
            tdata      = None

            if(fixed_data):
                tdata       = self.__fixed_value
            else:
                tdata       = self.update_target_random_data()

            self.target.doSetInputData(tdata)

            self.scope.runCapture()

            try:
                self.target.doRunExperiment()
            except Exception as e:
                print("Caught exception during TTest Capture: %s" % str(e))
                print("Continuing...")

            while(not self.scope.scopeReady()):
                pass

            trace = self.scope.getRawChannelData(
                self.signal_channel,
                self.num_samples
            )

            storedata = None
            
            if(self.store_input_with_trace):
                # Stored data is always passed as an np array.
                storedata = np.frombuffer(tdata,dtype=np.uint8)

            if(fixed_data):
                self.ts_fixed.writeTrace(trace,aux_data = storedata)
            else:
                self.ts_rand.writeTrace(trace,aux_data = storedata)

        self.ts_rand.flushTraces()
        self.ts_fixed.flushTraces()

    # ------------------

    @property
    def fixed_value(self):
        return self.__fixed_value

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

