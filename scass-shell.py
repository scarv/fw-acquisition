#!/usr/bin/python3


import sys
import secrets

import matplotlib.pyplot as plt

from tqdm import tqdm

import scass

class TestTTestCapture(scass.ttest.TTestCapture):
    
    def update_target_fixed_data(self):
        return b'\xa6K5\xe6P\xb7\x98I'

def main():

    # Connect to a target device
    print("Open target...")
    target                  = scass.comms.Target(
        "/dev/ttyUSB0",
        9600
    )

    print("Hello world...")
    assert(target.doHelloWorld())

    print("Experiment Init...")
    assert(target.doInitExperiment())

    print("Seed PRNG...")
    assert(target.doSeedPRNG(0xFFFFFFFF))

    print("Experiment Name: '%s'"%target.doGetExperiementName())

    input_data_len  = target.doGetInputDataLength()
    output_data_len = target.doGetOutputDataLength()

    wr_input_data   = secrets.token_bytes(input_data_len);
    wr_output_data  = secrets.token_bytes(output_data_len);

    target.doSetInputData(wr_input_data)
    target.doSetOutputData(wr_output_data)
    
    rd_input_data   = target.doGetInputData(input_data_len)
    rd_output_data  = target.doGetOutputData(output_data_len)

    print("Input Data Length : %d" % input_data_len)
    print("Wrote Input Data  : %s" % str(wr_input_data))
    print("Read Input Data   : %s" % str(rd_input_data))
    
    print("Output Data Length: %d" % output_data_len)
    print("Wrote Output Data : %s" % str(wr_output_data))
    print("Read Output Data  : %s" % str(rd_output_data))
    
    # Connect to the first picoscope5000 we find.
    scope                   = scass.scope.Picoscope5000()

    info                    = scope.scope_information

    chan_t                  = scope.getChannel("A")
    chan_s                  = scope.getChannel("B")

    chan_t.vrange           = 5
    chan_t.voffset          = 0
    chan_t.probeAttenuation = 1.0
    chan_t.coupling         = scass.scope.ScopeChannel.COUPLING_DC
    chan_t.enabled          = True

    chan_s.vrange           = 5
    chan_s.voffset          = 0
    chan_s.probeAttenuation = 1.0
    chan_s.coupling         = scass.scope.ScopeChannel.COUPLING_DC
    chan_s.enabled          = True
    
    trigger                 = scass.scope.ScopeTrigger(scope)
    trigger.src_channel     = chan_t.channel_id
    trigger.direction       = scass.scope.ScopeTrigger.RISING
    trigger.threshold_V     = 2.0
    trigger.timeout         = 10000
    trigger.enabled         = True

    scope.configureTrigger(trigger)

    scope.setSamplingResolution("8")

    nsamples                = 2000
    sample_freq,x           = scope.setSamplingFrequency(200e6, nsamples)
    nsamples                = min(nsamples,x)

    print("Actual sampling frequency: %s" % str(sample_freq))
    print("Number of samples per capture: %d"% nsamples)
    print("Waiting for capture...")

    tmpfile = "/tmp/traces.strs"
    tfile   = open(tmpfile,"wb")
    twriter = None
    dtype   = None

    for i in tqdm(range(0,100)):
        scope.runCapture()
        target.doRunExperiment()

        while(not scope.scopeReady()):
            pass

        signal_power            = scope.getRawChannelData(chan_s,nsamples)
        signal_trigger          = scope.getRawChannelData(chan_t,nsamples)
        window_size             = scope.findTriggerWindowSize(signal_trigger)
        
        if(twriter == None):
            twriter = scass.trace.TraceWriterSimple(
                tfile, dtype=signal_power.dtype
            )
            dtype = signal_power.dtype
            twriter.write_through = True

        twriter.writeTrace(signal_power)

    twriter.flushTraces()

    print("Longest trace: %d samples" % twriter.longest_trace)
    print("Trace data type: %s (%s)" % (dtype.name,dtype.str))


    # Do a short ttest.
    ts_fix_file = "/tmp/t-fix.strs"
    ts_rng_file = "/tmp/r-rnd.strs"

    ts_fix_wr = scass.trace.TraceWriterSimple(open(ts_fix_file,"wb"),dtype)
    ts_rng_wr = scass.trace.TraceWriterSimple(open(ts_rng_file,"wb"),dtype)

    ttest_capture = TestTTestCapture(
        target,
        scope,
        chan_t,
        chan_s,
        ts_fix_wr,
        ts_rng_wr,
        num_traces=100,
        num_samples=nsamples
    )

    ttest_capture.store_input_with_trace = True
    ttest_capture.runTTest()

    print("TTest Fixed Value: %s" % str(ttest_capture.fixed_value))
    
    ts_fix_wr.close()
    ts_rng_wr.close()

    print("Loading ttest traces...")
    ts_fix_rd = scass.trace.TraceReaderSimple(open(ts_fix_file,"rb"),dtype)
    ts_rng_rd = scass.trace.TraceReaderSimple(open(ts_rng_file,"rb"),dtype)

    ts_fix = scass.trace.TraceSet()
    ts_rng = scass.trace.TraceSet()

    ts_fix.loadFromTraceReader(ts_fix_rd)
    ts_rng.loadFromTraceReader(ts_rng_rd)

    ts_fix_rd.close()
    ts_rng_rd.close()

    print("Running TTest...")
    ttest = scass.ttest.TTest(ts_fix, ts_rng)

    print("Reading traces back...")

    tfile.close()
    tfile   = open(tmpfile,"rb")
    treader = scass.trace.TraceReaderSimple(tfile, dtype=dtype)
    
    trace_set = scass.trace.TraceSet()
    trace_set.loadFromTraceReader(treader)

    print("Traces Read: %d" % treader.traces_read)
    print("Uniform length: %s" % str(trace_set.traces_are_uniform_length))

    tmatrix = trace_set.tracesAs2dArray()
    tavg    = trace_set.averageTrace()   
        
    print("Trace length: %d" % trace_set.trace_length)
    print("Avg trace length: %d" % tavg.size)
    print("tmatrix shape: %s" % str(tmatrix.shape))

    plt.subplot(3,1,1)
    plt.plot(tmatrix, linewidth=0.1)
    
    plt.subplot(3,1,2)
    plt.plot(tavg   , linewidth=0.1)

    plt.subplot(3,1,3)
    plt.plot(ttest.ttrace, linewidth=0.1)

    plt.show()

if(__name__ == "__main__"):
    main()

