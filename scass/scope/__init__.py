
import time

from .Picoscope5000 import Picoscope5000
from .ScopeChannel  import ScopeChannel
from .ScopeTrigger  import ScopeTrigger
from .Scope         import fromConfig

def findTriggerWindowSize(scope, target, power_channel,max_retries = 10):
    """
    Work out how big the trigger window size is for a single trace.
    """

    sig_trigger = None
    sig_power   = None

    window_size = 0
    retries     = 0
    while(window_size <= 10 and retries < max_retries):
    
        scope.runCapture()
        target.doRunFixedExperiment()

        while(scope.scopeReady() == False):
            pass

        sig_trigger = scope.getRawChannelData(
            scope.trigger_channel, scope.max_samples)
        sig_power   = scope.getRawChannelData(
            power_channel,scope.max_samples)

        window_size = scope.findTriggerWindowSize(sig_trigger)
        retries += 1
    
        time.sleep(1)

    return window_size

