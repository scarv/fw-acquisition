#!/usr/bin/python3

import scass

import matplotlib.pyplot as plt

def main():
    
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

    sample_freq,nsamples    = scope.setSamplingFrequency(100e6, 1000)

    print("Actual sampling frequency: %s" % str(sample_freq))
    print("Number of samples per capture: %d"% nsamples)
    print("Waiting for capture...")
    scope.runCapture()

    while(not scope.scopeReady()):
        pass

    print("Getting captured data...")
    signal_power            = scope.getRawChannelData(chan_s)
    signal_trigger          = scope.getRawChannelData(chan_t)
    window_size             = scope.findTriggerWindowSize(signal_trigger)
    
    print("Got %d samples." % len(signal_power))

    print("Trigger window size: %d" % window_size)

    plt.plot(signal_power)
    plt.plot(signal_trigger)
    plt.show()

if(__name__ == "__main__"):
    main()

