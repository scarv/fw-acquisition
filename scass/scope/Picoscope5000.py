
import logging as log

try:
	from picoscope.ps5000a import PS5000a
except ModuleNotFoundError as m:
    log.warn("Picoscope.ps5000a module not found. Some scope functionality will be unavailable")

from .Scope import Scope
from .ScopeChannel import ScopeChannel
from .ScopeTrigger import ScopeTrigger

class Picoscope5000(Scope):
    """
    Scope object for the Picoscope5000 series 4-channel osiliscope.
    """

    def __init__(self, serialNumber=None):
        """
        Initialise the scope object.
        if serialNumber is specified, open that specific scope.
        """
        Scope.__init__(self)

        self.__scope        = PS5000a(serialNumber=serialNumber)

        self._channels["A"] = ScopeChannel(self,"A")
        self._channels["B"] = ScopeChannel(self,"B")
        self._channels["C"] = ScopeChannel(self,"C")
        self._channels["D"] = ScopeChannel(self,"D")


    def configureChannel(self, channel):
        """
        Configure the scope to reflect the channel configuration in the
        supplied channel object.
        """
        assert(isinstance(channel, ScopeChannel))

        coupling = "AC"
        if(channel.coupling == ScopeChannel.COUPLING_DC):
            coupling = "DC"
        elif(channel.coupling == ScopeChannel.COUPLING_DC):
            coupling = "AC"
        else:
            raise ValueError("Unknown channel coupling: %s"%channel.coupling)

        self.__scope.setChannel(
            channel         = channel.channel_id,
            coupling        = coupling,
            VRange          = channel.vrange,
            VOffset         = channel.voffset,
            enabled         = channel.enabled,
            BWLimited       = False,
            probeAttenuation= channel.probe_attenuation
        )


    def getRawChannelData(self, channel, numSamples = None):
        """
        Return the most recently captured raw signal data for the supplied 
        channel as a numpy array.
        Returns at most numSamples samples. If numSamples is zero, the
        maximum number of samples per capture are returned.
        If numSamples is None, then self.num_samples are returned.
        """
        assert(isinstance(channel,ScopeChannel))
        assert(channel.channel_id in self._channels)

        if(numSamples == None):
            numSamples = self._num_samples

        data, nsamples,overflow = self.__scope.getDataRaw(
            channel = channel.channel_id,
            numSamples = numSamples
        )

        return data

    def configureTrigger(self, trigger):
        """
        Configure a trigger signal for the scope.
        Note that for the Picoscope5000, the timeout field of the
        ScopeTrigger object should be an integer, representing miliseconds.
        """
        assert(isinstance(trigger, ScopeTrigger))

        self._trigger = trigger

        direction = "Rising"
        if(trigger.direction == ScopeTrigger.RISING):
            direction = "Rising"
        elif(trigger.direction == ScopeTrigger.FALLING):
            direction = "Falling"
        else:
            raise ValueError("Unknown trigger direction: %s"%\
                trigger.direction)

        self.__scope.setSimpleTrigger(
            trigger.src_channel.channel_id,
            threshold_V = trigger.threshold,
            direction   = direction,
            delay       = 0,
            timeout_ms  = trigger.timeout,
            enabled     = trigger.enabled
        )


    def setSamplingFrequency(self, sampleFreq,numSamples):
        """Set the desired sampling frequency. Return the actual
            sampling frequency"""
        freq, nsamples = self.__scope.setSamplingFrequency(
            sampleFreq,
            numSamples
        )
        self._max_samples = nsamples
        self._sample_freq = freq
        return freq


    def setSamplingResolution(self, resolution):
        """Set the resolution of the sample values"""
        self._resolution = resolution
        self.__scope.setResolution(resolution)


    def scopeReady(self):
        """Return true if the scope is ready to use. False otherwise."""
        return self.__scope.isReady()


    def runCapture(self):
        """Wait for the trigger to indicate some data was captured and
        then return. Use getRawChannelData to return the data."""
        self.__scope.runBlock()

    
    @property
    def scope_information(self):
        """Returns a device specific string detailing it. Usually a
          serial number."""
        return self.__scope.getAllUnitInfo()
