
import configparser

import numpy as np

import matplotlib.pyplot as plt

from . import ScopeChannel
from .ScopeTrigger import ScopeTrigger
from . import Picoscope5000

class Scope(object):
    """
    Base class of all scope connection classes
    """

    def __init__(self):
        """
        Initialise the new scope object.
        """
        self._channels     = {}
        self._max_samples  = 0
        self._num_samples  = 0
        self._trigger      = None
        self._resolution   = None
        self._sample_freq  = None

    @property
    def max_samples(self):
        """Get the maximum number of samples per trace, given the current
        scope configuration"""
        return self._max_samples

    @property
    def sample_freq(self):
        """Return the sampling frequency as a floating point number"""
        return self._sample_freq

    @sample_freq.setter
    def sample_freq(self,v):
        """Set the sampling frequency, also updates maximum samples per
        trace."""
        self._sample_freq = self.setSamplingFrequency(
            v, self._num_samples)

    @property
    def num_samples(self):
        """Samples to gather per trace"""
        return self._num_samples

    @num_samples.setter
    def num_samples(self,v):
        """Set the number of samples to gather per trace."""
        self._num_samples = min(self._max_samples,self._num_samples)

    @property
    def trigger_config(self):
        """Return the current trigger signal configuration"""
        return self._trigger
    
    @property
    def trigger_channel(self):
        """Return the channel the trigger uses"""
        return self._trigger.src_channel
    
    @property
    def resolution(self):
        """Scope sampling resolution"""
        return self._resolution

    @resolution.setter
    def resolution(self,v):
        """Set the sampling resolution of the scope"""
        self._resolution = v
        self.setSamplingResolution(v)

    def getChannel(self, cid):
        """Return the ScopeChannel object corresponding to the supplied cid"""
        return self._channels[cid]

    def dataReady(self):
        """
        Returns true if the scope has some captured data ready to be
        collected.
        """
        return False

    def configureChannel(self, channel):
        """
        Update the scope configuration according to the supplied channel
        object.
        """
        assert(isinstance(channel, ScopeChannel))
        raise NotImplementedError("Function should be implemented by inheriting classes")


    def getRawChannelData(self, channel, numSamples = None):
        """
        Return the most recently captured raw signal data for the supplied 
        channel as a numpy array.
        Returns at most numSamples samples. If numSamples is zero, the
        maximum number of samples per capture are returned.
        If numSamples is None, then self.num_samples are returned.
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
        self._trigger = trigger
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
        self._resolution = resolution
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

        threshold      = (np.max(trigger_signal) + np.min(trigger_signal))/2

        print("Trigger Threshold: %s" % str(threshold))

        tr = 0

        while(trigger_signal[tr] < threshold):
            tr += 1

        while(trigger_signal[tr] > threshold):
            tr += 1
        
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

    def dumpConfig(self, filepath):
        """
        Dump the current scope configuration out to a file.
        """
        
        config = configparser.ConfigParser()

        config["SCOPE"] = {
            "classType"     : self.__class__.__name__,
            "max_samples"   : self._max_samples,
            "num_samples"   : self._num_samples,
            "sample_freq"   : self._sample_freq,
            "resolution"    : self.resolution
        }

        for c in self._channels:
            channel = self._channels[c]
            config["CHANNEL_%s" % str(channel.channel_id)] = {
                "id"        : channel.channel_id,
                "coupling"  : channel.coupling,
                "enabled"   : channel.enabled,
                "voffset"   : channel.voffset,
                "vrange"    : channel.vrange,
                "probeatten": channel.probe_attenuation
            }

        config["TRIGGER"] = {
            "channel"  : self._trigger.src_channel.channel_id,
            "direction": self._trigger.direction,
            "threshold": self._trigger.threshold,
            "timeout"  : self._trigger.timeout,
            "enabled"  : self._trigger.enabled
        }

        
        with open(filepath,"w") as fh:

            config.write(fh)

    def loadConfig(self, filepath):
        """
        Load a scope configuration from a file.
        """

        config = configparser.ConfigParser()
        config.read(filepath)

        if(config["SCOPE"]["classType"] != self.__class__.__name__):
            raise TypeError("Config is for scope class '%s', but this class is of type '%s'" % (config["SCOPE"]["classType"], self.__class__.__name__))
            return

        self._max_samples = config["SCOPE"].getint("max_samples")
        self._num_samples = config["SCOPE"].getint("num_samples")
        self._sample_freq = config["SCOPE"].getfloat("sample_freq")

        self.setSamplingFrequency(self._sample_freq,self._num_samples)

        channels = [c for c in config.sections() if c.startswith("CHANNEL_")]

        for c in channels:
            cid = config[c]["id"]
            self._channels[cid].coupling          = config[c]["coupling"  ] 
            self._channels[cid].enabled  = config[c].getboolean("enabled")
            self._channels[cid].voffset  = config[c].getfloat("voffset")
            self._channels[cid].vrange   = config[c].getfloat("vrange" )
            self._channels[cid].probe_attenuation = \
                config[c].getfloat("probeatten")
            
            self.configureChannel(self._channels[cid])

        trigger = ScopeTrigger(self)

        trigger.src_channel = self.getChannel(config["TRIGGER"]["channel"])
        trigger.direction   = config["TRIGGER"]["direction"] 
        trigger.threshold   = config["TRIGGER"].getfloat("threshold")
        trigger.timeout     = config["TRIGGER"].getint("timeout") 
        trigger.enabled     = config["TRIGGER"].getboolean("enabled")
        
        self.configureTrigger(trigger)

        self.setSamplingResolution(config["SCOPE"]["resolution"])


def fromConfig(filepath):
    """
    Create a scope class instance of the appropriate type and
    configure it based on the supplied config file path.
    """

    config = configparser.ConfigParser()
    config.read(filepath)
    
    stype = config["SCOPE"]["classType"]

    scopetypes = {
        "Picoscope5000": Picoscope5000.Picoscope5000
    }

    scope = scopetypes[stype]()

    scope.loadConfig(filepath)

    return scope

