
import numpy as np

import matplotlib.pyplot as plt

from . import ScopeChannel

class Scope(object):
    """
    Base class of all scope connection classes
    """

    def __init__(self):
        """
        Initialise the new scope object.
        """
        self._channels     = {}
        self._max_samples  = -1

    @property
    def max_samples(self):
        """Get the maximum number of samples per trace, given the current
        scope configuration"""
        return self._max_samples

    def getChannel(self, cid):
        """Return the ScopeChannel object corresponding to the supplied cid"""
        return self._channels[cid]


    def configureChannel(self, channel):
        """
        Update the scope configuration according to the supplied channel
        object.
        """
        assert(isinstance(channel, ScopeChannel))
        raise NotImplementedError("Function should be implemented by inheriting classes")


    def getRawChannelData(self, channel, numSamples = 0):
        """
        Return the most recently captured raw signal data for the supplied 
        channel as a numpy array.
        Returns at most numSamples samples. If numSamples is zero, the
        maximum number of samples per capture are returned.
        """
        assert(isinstance(channel,ScopeChannel))
        assert(channel in self._channels)
        raise NotImplementedError("Function should be implemented by inheriting classes")
        return np.zeros(1,dtype=int)


    def scopeReady(self):
        """Return true if the scope is ready to use. False otherwise."""
        raise NotImplementedError("Function should be implemented by inheriting classes")
        return False

    def configureTrigger(self, trigger):
        """Configure a channel as a trigger signal"""
        raise NotImplementedError("Function should be implemented by inheriting classes")

    @property
    def channels(self):
        """Return a list of channel ids which can be used in get_channel
        or configure_channel"""
        return list(self._channels.keys())

    
    @property
    def num_channels(self):
        """Return the number of channels this scope supports. """
        return len(self._channels)

    @property
    def scope_information(self):
        """Returns a device specific string detailing it. Usually a
          serial number."""
        raise NotImplementedError("Function should be implemented by inheriting classes")
        return "Not Implemented"


    def setSamplingFrequency(self, sampleFreq, numSamples):
        """Set the desired sampling frequency. Return the actual
            sampling frequency"""
        raise NotImplementedError("Function should be implemented by inheriting classes")
        return 0

    def setSamplingResolution(self, resolution):
        """Set the resolution of the sample values"""
        raise NotImplementedError("Function should be implemented by inheriting classes")
    
    
    def runCapture(self):
        """Wait for the trigger to indicate some data was captured and
        then return. Use getRawChannelData to return the data."""
        raise NotImplementedError("Function should be implemented by inheriting classes")


    def findTriggerWindowSize(self, trigger_signal):
        """
        First finds the mean value of a trigger signal trace, then
        counts the number of samples in the signal above that value and
        returns it.
        This represents the number of samples in the signal which fall
        inside the trigger window.
        Assumes:
        - No trigger sample offset.
        - The trigger window is a region where the trigger is "high"
        """

        threshold      = np.mean(trigger_signal)

        print("Trigger Threshold: %s" % str(threshold))

        tr = trigger_signal.size - 1

        while(trigger_signal[tr] < threshold and tr > 1):
            tr -= 1

        tr = min(trigger_signal.size-1,tr+100)
        
        return tr

    def plotSingleCapture(self, target,nsamples):
        """
        Plot a single experiment run and display it.
        Shows the trigger signal and power signal overlayed in the
        same plot.
        """

        self.runCapture()
        target.doRunExperiment()

        while(not self.scopeReady()):
            pass

        traces = [self.getRawChannelData(c,nsamples) for c in self._channels.values()]

        plt.clf()
        
        for t in traces:
            plt.plot(t, linewidth=0.1)

        plt.show()

