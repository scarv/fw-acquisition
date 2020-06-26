
import random
import secrets
import time
import os

import logging as log

import numpy as np

from tqdm    import tqdm

from ..comms import Target
from ..scope.Scope import Scope
from ..scope.ScopeChannel import ScopeChannel

class CollectTraces(object):
    """
    A class for collecting N traces for later use in a CPA attack.
    """

    def __init__(
            self,
            target,
            scope,
            trigger_channel,
            signal_channel,
            num_traces  = 1000,
            num_samples = 1000,
            trs_dtype  = np.float32
        ):
        """
        Create a new CollectTraces object

        Parameters:

        target - scass.comms.Target
            Class used to communicate with the target device

        scope - scass.scope.Sope
            Oscilliscope control object.

        trigger_channel - scass.scope.ScopeChannel
            The scope channel setup as the trigger.

        signal_channel - scass.scope.ScopeChannel
            The scope channel setup as the signal to capture.
        
        num_traces : int
            The number of traces to capture in total.
        
        num_samples: int
            The numer of samples to capture per trace.
        """

        assert(isinstance(target, Target))
        assert(isinstance(scope, Scope))
        assert(isinstance(trigger_channel, ScopeChannel))
        assert(isinstance(signal_channel, ScopeChannel))
        assert(isinstance(num_traces,int))

        self.target         = target
        self.scope          = scope
        self.trigger_channel= trigger_channel
        self.signal_channel = signal_channel
        
        self.traces         = np.zeros(
            (num_traces,num_samples),
            dtype=trs_dtype
        )

        self.num_samples    = num_samples
        self.num_traces     = num_traces
        self.trace_count    = 0
        
        # Target clock information. Populated in _pre_run_ttest
        self.target_clk_info= None

        # Target variable information, populated by _getTargetVarInformation
        self.tgt_var_num    = 0
        self.tgt_vars       = []
        # Dict of np.ndarray, keyed by target input variable names.
        self.tgt_vars_values= {}
        
        self.tgt_randomness_size = 0
        self.tgt_randomness_rate = 0
        self.tgt_randomness_count= 0
    
    def getVariableValuesForTraces(self, varname):
        return self.tgt_vars_values[varname]
    

    def getVariableByName(self, name):
        """
        Return a reference to the object repesenting an experiment variable
        with the given name.
        Must be called after _get_target_var_information is called.
        """
        for var in self.tgt_vars:
            if(var.name == name):
                return var

        assert(False) ,"No variable with name '%s' exists." % name


    def _updateTargetRandomness(self):
        """
        Update the randomness array data on the target device.
        """

        tosend = secrets.token_bytes(self.tgt_randomness_size)

        return self.target.doRandSeed(tosend)
    

    def _getTargetVarInformation(self):
        """
        Gather information from the target device about which target
        variables need to be managed and how.
        Called by _initialise
        """

        log.info("Getting target variable information")

        self.tgt_var_num  = self.target.doGetVarNum()

        log.info("- %d variables" % self.tgt_var_num)
        
        assert(self.tgt_var_num != False)

        for i in range(0,self.tgt_var_num):

            var = self.target.doGetVarInfo(i)

            assert(var != False)

            self.tgt_vars.append(var)

            self.tgt_vars_values[var.name] = np.zeros (
                (self.num_traces, var.size),
                dtype=np.uint8
            )
        
            log.info("- Var: %20s (%d bytes)" % (var.name, var.size))

        self.tgt_randomness_size = self.target.doRandGetLen()
        self.tgt_randomness_rate = self.target.doRandGetRefreshRate()
        self.tgt_randomness_count= 0


    def initialiseTraceCollection(self):
        """
        Must be called once before calling gatherTraces.
        Populates information about target variables.
        """
        self._getTargetVarInformation()

        self.scope.num_samples = self.num_samples


    def _setupVariableValues(self):
        """
        Make sure all input variable values have their correct
        values set.
        """
        for var in self.tgt_vars:

            if(var.current_value == None):
                var.randomiseValue()
                var.setFixedValue(var.current_value)

            log.info("- Set %20s = %s" % (var.name, var.fixed_value))
            self.target.doSetVarFixedValue(var.vid, var.fixed_value)
            self.target.doSetVarValue     (var.vid, var.fixed_value)


    def _preGatherTrace(self, i):
        """
        Randomise all of the variable values which need it, and
        update the target randomness pool.
        """
        for var in self.tgt_vars:
            if(var.is_input and var.is_randomisable):
                var.randomiseValue()
                var.setFixedValue(var.current_value)
                self.target.doSetVarValue(var.vid, var.current_value)

    def _gatherTrace(self, i):
        """
        Collect a single trace.
        """
        self.scope.runCapture()
        self.target.doRunRandomExperiment()

        while(not self.scope.dataReady()):
            pass

        new_trace = self.scope.getRawChannelData (
            self.signal_channel,
            numSamples = self.num_samples
        )
        
        # Store the new trace
        self.traces[self.trace_count] = new_trace
        
        # Capture the variable values
        for var in self.tgt_vars:
            for i in range(0,var.size):
                self.tgt_vars_values[var.name][self.trace_count][i] = \
                    var.current_value[i]


    def _postGatherTrace(self, i):
        """
        Called after _gatherTrace. Update the target randomness pool
        if needed.
        """
        self.tgt_randomness_count += 1

        if(self.tgt_randomness_count > self.tgt_randomness_rate):
            if(self.tgt_randomness_rate > 0):
                self._update_target_randomness()
        
        self.trace_count += 1


    def gatherTraces(self):
        """
        Performs the trace gathering procedure.
        """

        self._setupVariableValues()

        log.info("Gathering Traces...")

        for i in tqdm(range(0,self.num_traces)):
            self._preGatherTrace(i)
            self._gatherTrace(i)
            self._postGatherTrace(i)
