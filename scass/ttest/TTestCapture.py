
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
        assert(isinstance(num_traces,int))

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

    
    def reportVariables(self):
        """
        Print information about each managed variable on the target device.
        """

        log.info("%3s | %20s | %5s | %6s | %6s | %12s | %5s" % (
            "vid",
            "name",
            "size",
            "input",
            "output",
            "randomisable",
            "ttest"
        ))
        log.info("-"*80)
        
        for var in self.tgt_vars:

            log.info("%3d | %20s | %5d | %6s | %6s | %12s | %5s" % (
                var.vid,
                var.name,
                var.size,
                var.is_input,
                var.is_output,
                var.is_randomisable,
                var.is_ttest_variable
            ))


    def _initialise(self):
        """
        Called once before performTTest. Does any one-time configuration
        needed by the target or host.
        """
        self._get_target_var_information()

        # Make sure the scope knows how many data points to capture
        self.scope.num_samples = self.num_samples

    def _get_target_var_information(self):
        """
        Gather information from the target device about which target
        variables need to be managed and how.
        Called by _initialise
        """

        self.tgt_var_num  = self.target.doGetVarNum()
        
        assert(self.tgt_var_num != False)

        self.tgt_vars       = []
        self.tgt_vars_ttest = []

        for i in range(0,self.tgt_var_num):

            var = self.target.doGetVarInfo(i)

            assert(var != False)

            self.tgt_vars.append(var)

            if(var.is_randomisable and var.is_ttest_variable):
                self.tgt_vars_ttest.append(var)


    def _assign_ttest_fixed_values(self):
        """
        Assigns fixed values to all managable variables which are
        both randomisable and ttest variables.
        """

        if(len(self.tgt_vars_ttest) > 0):
            log.info("%20s | Fixed Value" % "Variable")
            log.info("-"*80)

        for var in self.tgt_vars_ttest:
                
            fixed_val = secrets.token_bytes(var.size)
            var.setFixedValue(fixed_val)

            log.info("%20s | %s" % (
                var.name,
                hex(int.from_bytes(var.fixed_value,byteorder="little"))
            ))



    def _pre_run_ttest(self):
        """
        Called immediately before the main _run_ttest function is
        called.
        """
        self._assign_ttest_fixed_values()


    def _pre_gather_trace(self):
        """
        Called immediately before any new trace (fixed or random)
        is gathered.
        Called before _pre_gather_fixed_value_trace and
                      _pre_gather_random_value_trace
        """


    def _pre_gather_fixed_value_trace(self):
        """
        Gathers a single trace where all TTest variables take on
        their fixed values.
        """
        for var in self.tgt_vars_ttest:
            var.takeFixedValue()
            self.target.doSetVarValue(var.vid, var.fixed_value)

    
    def _pre_gather_random_value_trace(self):
        """
        Gathers a single trace where all TTest variables take on
        their random values.
        """
        for var in self.tgt_vars_ttest:
            var.randomiseValue()
            self.target.doSetVarValue(var.vid, var.current_value)

    
    def _gather_trace(self):
        """
        Gather a single trace from the target device.
        """
        self.scope.runCapture()
        
        self.target.doRunExperiment()

        trace = self.scope.getRawChannelData(
            self.signal_channel,
            numSamples = self.num_samples
        )

        return trace


    def _post_gather_trace(self, new_trace, gather_fixed):
        """
        Called after each new trace (fixed or random) is gathered.
        Responsible for trace post-processing and adding traces to
        the relevent sets.

        :param new_trace:
            The newly gathered trace as an np.ndarray

        :param gather_fixed:
            A bool. True iff a fixed value trace, false if random value.
        """
        if(gather_fixed):
            self.ts_fixed.writeTrace(new_trace,None)
        else:
            self.ts_rand.writeTrace(new_trace,None)


    def _run_ttest(self):
        """
        Top level function which gathers the requisite number of traces
        for the TTest sets.
        """

        for i in self.__progress_bar_func(range(0,self.num_traces)):

            self._pre_gather_trace()

            new_trace       = None
            gather_fixed    = random.choice([True,False])

            if(gather_fixed):
                self._pre_gather_fixed_value_trace()
            else:
                self._pre_gather_random_value_trace()

            new_trace = self._gather_trace()
            
            self._post_gather_trace(new_trace, gather_fixed)


    def _post_run_ttest(self):
        """
        Called after the main ttest function finishes. Can be used
        for trimming collected data or cleanup.
        """


    def initialiseTTest(self):
        """
        Publically visible initialisation funciton. Wraps _initialise
        """
        self._initialise()


    def performTTest(self):
        """
        Runs the entire TTest procedure.
        """
        self._pre_run_ttest()
        self._run_ttest()
        self._post_run_ttest()


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

