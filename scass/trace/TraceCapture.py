
import random
import secrets

import logging as log

import numpy as np

from tqdm    import tqdm

from ..comms import Target
from ..scope.Scope import Scope
from ..scope.ScopeChannel import ScopeChannel
from ..trace import TraceWriterBase

def no_progress_bar(x):
    return x

class TraceCapture(object):
    """
    A class which automates the capture process for trace sets.
    """


    def __init__(self, 
                 target,
                 scope,
                 trigger_channel,
                 signal_channel,
                 trace_set,
                 num_traces,
                 num_samples):
        """
        Create a new trace capture class.
        
        Parameters:
        target - scass.comms.Target
            Class used to communicate with the target device

        scope - scass.scope.Sope
            Oscilliscope control object.

        trigger_channel - scass.scope.ScopeChannel
            The scope channel setup as the trigger.

        signal_channel - scass.scope.ScopeChannel
            The scope channel setup as the signal to capture.

        trace_set - scass.trace.TraceWriterBase
            Trace set container

        num_traces : int
            The number of traces to capture in total.

        num_samples: int
            The numer of samples to capture per trace.
        """

        assert(isinstance(target, Target))
        assert(isinstance(scope, Scope))
        assert(isinstance(trigger_channel, ScopeChannel))
        assert(isinstance(signal_channel, ScopeChannel))
        assert(isinstance(trace_set, TraceWriterBase))

        self.__progress_bar     = True
        self.__progress_bar_func= tqdm

        self.target         = target
        self.scope          = scope
        self.trigger_channel= trigger_channel
        self.signal_channel = signal_channel
        self.trace_set      = trace_set

        self.num_samples    = num_samples
        self.num_traces     = num_traces
        self.min_traces     = num_traces/2

        # Store test input data with each trace?
        self.store_input_with_trace = False

        # Length of experiment data array on the target.
        self.input_data_len = None

        self.expect_fixed_data_len=-1

    def prepareCapture(self):
        """
        Called once at the start of the data capture, used to gather
        information on the target.
        - Gets length of input data
        - Runs the target.doInitExperiment() function
        - Generates a *random* fixed value to use.
        Returns true if preparation succeeded, False otherwise.
        """

        # Get the length of the target experiment data array.
        self.input_data_len = self.target.doGetInputDataLength()
        
        try:
            self.target.doInitExperiment()
        except Exception as e:
            log.error("Failed to initialise experiment: %s" % str(e))
            return False

        return True

    def preTraceAcquire(self):
        """
        Called prior to each trace acquisition and selection of
        data for that trace.
        Can be used to update masks and such.
        """
        pass


    def getNewData(self):
        """
        Called for each acquision. Generates the input data for the
        device.
        """
        return bytes(self.input_data_len)

    def runCapture(self):
        """
        Runs the trace data capture.
        """

        for i in self.__progress_bar_func(range(0,self.num_traces)):

            self.preTraceAcquire()
            
            tdata       = self.getNewData()

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

            self.trace_set.writeTrace(trace,aux_data = storedata)

        self.trace_set.flushTraces()

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
            self.__progress_bar_func = no_progress_bar

