
"""
File containing classes and functions for interfacing with the power
measurement scope.
"""

import os
import sys
import logging as log

from picoscope import ps5000a


class SassScope:
    """
    Main class which wraps around the scope
    """

    def __init__(self):
        """
        Setup a scope.
        """
        self.scope = None
        
    def OpenScope(self):
        """
        Open a connection to a scope.
        """
        self.scope = ps5000a.PS5000a()
        log.info("Connected to scope:\n"+self.scope.getAllUnitInfo())

    def CloseScope(self):
        """
        Close the scope connection
        """
        log.info("Closing scope connection")
        self.scope.close()
