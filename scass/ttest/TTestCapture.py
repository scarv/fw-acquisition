
import random
import secrets
import time
import os

import logging as log

import gzip
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
                 traces_file,
                 fixed_file,
                 num_traces = 1000,
                 num_samples= 1000,
                 trs_dtype  = np.float32):
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

        traces_file - str
            File path to store traces too.
        
        fixed_file - str
            File name for fixed traces mask array.

        num_traces : int
            The number of traces to capture in total.

        num_samples: int
            The numer of samples to capture per trace.
        """

        assert(isinstance(target, Target))
        assert(isinstance(scope, Scope))
        assert(isinstance(trigger_channel, ScopeChannel))
        assert(isinstance(signal_channel, ScopeChannel))
        assert(isinstance(traces_file, str) or traces_file == None)
        assert(isinstance(fixed_file, str)  or fixed_file == None)
        assert(isinstance(num_traces,int))

        self.__progress_bar     = True
        self.__progress_bar_func= tqdm

        self.target         = target
        self.scope          = scope
        self.trigger_channel= trigger_channel
        self.signal_channel = signal_channel

        self.trs_file       = traces_file
        self.trs_fb_file    = fixed_file

        self.traces         = np.zeros(
            (num_traces,num_samples),
            dtype=trs_dtype
        )

        self.fixed_bits     = np.zeros(
            (num_traces), dtype=np.int8
        )

        # Dict of np.ndarray, keyed by target input variable names.
        self.tgt_vars_values= {}

        self.num_samples    = num_samples
        self.num_traces     = num_traces
        
        # Increments with each call to _post_gather_trace
        self.trace_count    = 0
        self.fixed_count    = 0
        self.rand_count     = 0

        self.zeros_as_fixed_value = False

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

            self.tgt_vars_values[var.name] = np.zeros (
                (self.num_traces, var.size),
                dtype=np.uint8
            )

        self.tgt_randomness_size = self.target.doRandGetLen()
        self.tgt_randomness_rate = self.target.doRandGetRefreshRate()
        self.tgt_randomness_count= 0


    def _update_target_randomness(self):
        """
        Update the randomness array data on the target device.
        """

        tosend = secrets.token_bytes(self.tgt_randomness_size)

        return self.target.doRandSeed(tosend)


    def _assign_ttest_fixed_values(self):
        """
        Assigns fixed values to all managable variables which are
        both randomisable and ttest variables.
        """

        if(len(self.tgt_vars) > 0):
            log.info("vid | %20s | Fixed Value" % "Variable")
            log.info("-"*80)

        for var in self.tgt_vars:

            if(var.is_input and var.is_ttest_variable):
                fixed_val = None

                if(self.zeros_as_fixed_value):
                    fixed_val = (0).to_bytes(var.size,byteorder="little")
                else:
                    fixed_val = secrets.token_bytes(var.size)

                var.setFixedValue(fixed_val)

            self.target.doSetVarFixedValue(var.vid, var.fixed_value)
            self.target.doSetVarValue     (var.vid, var.fixed_value)

            log.info("%3s | %20s | %s" % (
                var.vid ,
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
        # No need to do anything since fixed values are already
        # On the target device.
        for var in self.tgt_vars_ttest:
            var.takeFixedValue()


    def _pre_gather_random_value_trace(self):
        """
        Gathers a single trace where all TTest variables take on
        their random values.
        """
        for var in self.tgt_vars_ttest:
            if(var.is_randomisable):
                var.randomiseValue()
                self.target.doSetVarValue(var.vid, var.current_value)

    
    def _gather_trace(self, fixed):
        """
        Gather a single trace from the target device.
        """
        self.scope.runCapture()
        
        if(fixed):
            self.target.doRunFixedExperiment()
        else:
            self.target.doRunRandomExperiment()

        while(not self.scope.dataReady()):
            pass

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
            self.fixed_bits[self.trace_count] = 1
            self.fixed_count                 += 1
        else:
            self.fixed_bits[self.trace_count] = 0
            self.rand_count                  += 1
        
        self.traces [self.trace_count] = new_trace

        for var in self.tgt_vars_ttest:
            for i in range(0,var.size):
                self.tgt_vars_values[var.name][self.trace_count][i] = \
                    var.current_value[i]
                

        self.tgt_randomness_count += 1

        if(self.tgt_randomness_count > self.tgt_randomness_rate):
            if(self.tgt_randomness_rate > 0):
                self._update_target_randomness()

        self.trace_count += 1


    def _run_ttest(self):
        """
        Top level function which gathers the requisite number of traces
        for the TTest sets.
        """

        self.target.doInitExperiment()

        for i in self.__progress_bar_func(range(0,self.num_traces)):

            self._pre_gather_trace()

            new_trace       = None
            gather_fixed    = random.choice([True,False])

            if(gather_fixed):
                self._pre_gather_fixed_value_trace()
            else:
                self._pre_gather_random_value_trace()

            new_trace = self._gather_trace(gather_fixed)
            
            self._post_gather_trace(new_trace, gather_fixed)


    def _post_run_ttest(self):
        """
        Called after the main ttest function finishes. Can be used
        for trimming collected data or cleanup.
        Dumps all TTest variable values and traces to file.
        """

        log.info("%d Traces Captured: %d Fixed, %d Random." % (
            self.trace_count, self.fixed_count, self.rand_count
        ))

        fixed_trace_idx = np.nonzero(self.fixed_bits >= 1)
        rand_trace_idx  = np.nonzero(self.fixed_bits <  1)

        start = time.time()
        
        if(self.trs_file != None):
            log.info("Dumping %d traces to %s" % (
                self.traces.shape[0], self.trs_file))
            
            gzfh = gzip.GzipFile(self.trs_file,"w")
            np.save(file=gzfh, arr=self.traces)
            
            log.info("Dumped %d traces in %s seconds" % (
                self.traces.shape[0],
                (time.time()-start)))

            vdir    = os.path.dirname(self.trs_file)

            for var in self.tgt_vars:

                fp     = os.path.join(vdir,"var-" + var.name + ".npy.gz")
                values = self.tgt_vars_values[var.name]
                count  = self.tgt_vars_values[var.name].shape[0]

                log.info("Dumping %d input var %s values to %s" % (
                    count, var.name, fp
                ))
                gzfh = gzip.GzipFile(fp,"w")
                np.save(file=gzfh, arr=self.tgt_vars_values[var.name])

        if(self.trs_fb_file != None):
            log.info("Dumping fixed/random indicators to %s" % self.trs_fb_file)
            gzfh = gzip.GzipFile(self.trs_fb_file,"w")
            np.save(file=gzfh, arr=self.fixed_bits)
        

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

