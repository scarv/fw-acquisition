
from . import Scope

class ScopeChannel(object):
    """
    Abstract way of representing a scope channel configuration
    """

    COUPLING_DC = "DC"
    COUPLING_AC = "AC"

    def __init__(self, scope, channel_id):
        """
        Create the basic set of scope channel properties
        """

        assert(isinstance(scope, Scope.Scope))
        
        self._id = channel_id
        self._coupling = ScopeChannel.COUPLING_DC
        self._enabled  = False
        self._voffset  = 0
        self._vrange   = 5
        self._probe_attenuation = 1.0

        self._scope    = scope

    @property
    def scope(self):
        """Return the scope object associated with this channel"""
        return self._scope
    
    @property
    def channel_id(self):
        return self._id
    
    @property
    def enabled(self):
        """Is the channel enabled?"""
        return self._enabled

    @property
    def coupling(self):
        """AC or DC coupling?"""
        return self._coupling

    @property
    def voffset(self):
        """DC Voltage offset"""
        return self._voffset

    @property
    def vrange(self):
        """Voltage measurement range"""
        return self._vrange

    @property
    def probe_attenuation(self):
        return self._probe_attenuation

    @enabled.setter
    def enabled(self,v):
        """Is the channel enabled?"""
        assert(isinstance(v,bool))
        self._enabled = v
        self._scope.configureChannel(self)

    @coupling.setter
    def coupling(self,v):
        """AC or DC coupling?"""
        assert(v == ScopeChannel.COUPLING_DC or v == ScopeChannel.COUPLING_AC)
        self._coupling = v
        self._scope.configureChannel(self)

    @voffset.setter
    def voffset(self, v):
        """DC Voltage offset"""
        assert(isinstance(v,int) or isinstance(v,float))
        self._voffset = v
        self._scope.configureChannel(self)

    @vrange.setter
    def vrange(self,v):
        """Voltage measurement range"""
        assert(isinstance(v,int) or isinstance(v,float))
        self._vrange = v
        self._scope.configureChannel(self)
    
    @probe_attenuation.setter
    def probe_attenuation(self,v):
        assert(isinstance(v,float))
        self._probe_attenuation = v
        self._scope.configureChannel(self)

