
from picoscope.ps5000a import PS5000a

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


    def getRawChannelData(self, channel):
        """
        Return the most recently captured raw signal data for the supplied 
        channel as a numpy array.
        """
        assert(isinstance(channel,ScopeChannel))
        assert(channel.channel_id in self._channels)

        data, nsamples,overflow = self.__scope.getDataRaw(
            channel = channel.channel_id,
        )

        return data

    def configureTrigger(self, trigger):
        """
        Configure a trigger signal for the scope.
        Note that for the Picoscope5000, the timeout field of the
        ScopeTrigger object should be an integer, representing miliseconds.
        """
        assert(isinstance(trigger, ScopeTrigger))

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
        return (freq,nsamples)


    def setSamplingResolution(self, resolution):
        """Set the resolution of the sample values"""
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
