
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
