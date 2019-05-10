#!/usr/bin/python3


import sys
import secrets

from tqdm import tqdm

import scass

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

    edata_len = target.doGetExperiementDataLength()
    print("Experiment data size: %d" % edata_len)
    
    print("Randomising experiment data (%d)..."%edata_len)
    send_data = secrets.token_bytes(edata_len)
    target.doSetExperimentData(send_data)

    print("Reading experiment data (%d)..."%edata_len)
    recv_data = target.doGetExperiementData(edata_len)
    
    print("- Send: %s" % str(send_data))
    print("- Recv: %s" % str(recv_data))
    
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
    print("Reading traces back...")

    tfile.close()
    tfile   = open(tmpfile,"rb")
    treader = scass.trace.TraceReaderSimple(tfile, dtype=dtype)
    treader.readTraces()
    
    print("Traces Read: %d" % treader.traces_read)

    import matplotlib.pyplot as plt

    for t in treader.traces:

        plt.plot(t, linewidth=0.1)

    plt.show()

if(__name__ == "__main__"):
    main()

