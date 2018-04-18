
"""
File containing classes and functions for representing and operating
on a single trace.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt


class SassTrace:
    """
    Represents a single trace capture
    """

    def __init__(self,
                 trace_data,
                 key     = None,
                 message = None ):
        """
        Create a new SassTrace object.
        """
        self.data   = trace_data
        self.key    = key
        self.message= message


    def hasMessage(self):
        return self.message != None

    def hasKey(self):
        return self.key != None

    def __len__(self):
        return len(self.data)

    def __str__(self):
        tr = "%s,%s" % (self.key, self.message)
        for i in self.data:
            tr += ",%s" % i
        return tr
