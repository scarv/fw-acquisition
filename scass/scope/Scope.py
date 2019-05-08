
import numpy as np

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


    def getRawChannelData(self, channel):
        """
        Return the most recently captured raw signal data for the supplied 
        channel as a numpy array.
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
        Finds the index of the last sample in the trigger signal which 
        falls below 50% its maximum value.
        param trigger_signal is a numpy array.
        """

        threshold = np.amax(trigger_signal) / 4

        print("Max value: %d" % np.amax(trigger_signal))
        print("T   value: %d" % threshold)

        hi  = len(trigger_signal) - 1

        while(trigger_signal[hi] < threshold):
            hi = hi - 1
        
        return  hi
        
