
import random

import numpy as np

from tqdm import tqdm

from .SassTrace      import SassTrace
from .SassStorage    import SassStorage
from .SassEncryption import SassEncryption

class SAFTTestCapture(object):
    """
    Captures the two sets of trace data needed to perform leakage detection
    using T-tests.
    """


    def __init__(self,comms, scope, num_traces=10000):
        """
        Create a new TTest Capture object.

        :param SassComms comms: The object used to communicate with the
            target device.
        :param SassScope scope: The oscilliscope object to get traces from.
        :param int num_traces: The number of traces overall to capture.
        """

        self.comms       = comms
        self.edec        = SassEncryption()
        self.scope       = scope
        
        self.num_traces  = num_traces

        self.set1        = SassStorage()
        self.set2        = SassStorage()

        self.key         = self.edec.GenerateKeyBits(size   = 16)
        self.set1_msg    = self.edec.GenerateMessage(length = 16)

    def TotalTraces(self):
        """
        Return the total number of traces captured in both sets.
        """
        return len(self.set1) + len(self.set2)

    def RunCapture(self):
        """
        Runs the capture process on the target device.
        """

        # Setup the key.
        self.comms.doSetKey(self.key)

        dropped_traces = 0

        for i in tqdm(range(self.num_traces)):

            current_msg = None 
            rbit        = random.getrandbits(1)

            if(rbit):
                # Add to set 1 with a fixed message
                current_msg = self.set1_msg
            else:
                # Add to set 2 with a random message
                current_msg = self.edec.GenerateMessage(length=16)

            self.comms.doSetMsg(current_msg)

            self.scope.StartCapture()

            self.comms.doEncrypt()

            self.scope.WaitForReady()

            tracedata = self.scope.GetData(self.scope.sample_channel)

            if(tracedata[0] == None):
                dropped_traces += 1

            elif(rbit):
                # Add to set 1
                t = SassTrace(tracedata, self.key, current_msg)
                self.set1.AddTrace(t)

            else:
                # Add to set 2
                t = SassTrace(tracedata, self.key, current_msg)
                self.set2.AddTrace(t)

        return dropped_traces

