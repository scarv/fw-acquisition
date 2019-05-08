
from . import Scope

class ScopeTrigger(object):
    """Storage for a trigger signal configuration"""

    RISING = "Rising"
    FALLING= "Falling"

    def __init__(self, scope):
        
        assert(isinstance(scope, Scope.Scope))
        
        self._scope         = scope
        self._src_channel   = None
        self._direction     = ScopeTrigger.RISING
        self._threshold     = 1.0
        self._timeout       = 100
        self._enabled       = False
    
    @property
    def scope(self):
        """Return the scope object associated with this channel"""
        return self._scope

    @property
    def src_channel(self):
        """The ScopeChannel object this trigger overlays"""
        return self._src_channel

    @property
    def direction(self):
        """Direction the signal should be travelling to cause a trigger"""
        return self._direction

    @property
    def threshold(self):
        """Voltage threshold to cross when triggering"""
        return self._threshold

    @property
    def timeout(self):
        """How long to wait for the trigger before returning. This is
        very scope dependent"""
        return self._timeout
    
    @property
    def enabled(self):
        """Is the channel enabled?"""
        return self._enabled

    @enabled.setter
    def enabled(self,v):
        """Is the channel enabled?"""
        assert(isinstance(v,bool))
        self._enabled = v

    @src_channel.setter
    def src_channel(self,v):
        """The ScopeChannel object this trigger overlays"""
        if(isinstance(v,ScopeChannel)):
            assert(v.channel_id in self._scope.channels)
            self._src_channel = v
        else:
            assert(v in self._scope.channels)
            self._src_channel = self.__scope.get_channel(v)

    @direction.setter
    def direction(self,v):
        """Direction the signal should be travelling to cause a trigger"""
        assert(v in [ScopeTrigger.RISING, ScopeTrigger.FALLING])
        self._direction = v

    @threshold.setter
    def threshold(self, v):
        """Voltage threshold to cross when triggering"""
        assert(isinstance(v,float))
        self._threshold = v

    @timeout.setter
    def timeout(self,v):
        """How long to wait for the trigger before returning. This is
        very scope dependent"""
        assert(isinstance(v,float) or isinstance(v,int))
        self._timeout = v
