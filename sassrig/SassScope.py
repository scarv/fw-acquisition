
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

        self.trigger_channel    = "B"
        self.trigger_threshold  = 1.5
        self.trigger_direction  = "Rising"
        self.trigger_timeout    = 1000

        self.no_of_captures     = 1

        self.sample_channel     = "A"
        self.sample_range       = 1.0
        self.sample_coupling    = "DC"
        self.sample_interval    = 0.0001
        self.sample_duration    = 1000
        
    def OpenScope(self):
        """
        Open a connection to a scope.
        """
        self.scope = ps5000a.PS5000a()
        log.info("Connected to scope:\n"+self.scope.getAllUnitInfo())

    def ConfigureScope(self):
        """
        Used to write configuration of channels and triggers to the
        scope.
        """
        log.info("Configuring Scope...")
        log.info(" - Trigger Channel:   %s" % self.trigger_channel)
        log.info(" - Trigger Threshold: %d V" % self.trigger_threshold)
        log.info(" - Trigger Direction: %s" % self.trigger_direction)
        log.info(" - Trigger Timeout:   %d ms" % self.trigger_timeout)
        
        self.scope.setSimpleTrigger(
            self.trigger_channel,
            threshold_V = self.trigger_threshold,
            direction   = self.trigger_direction,
            timeout_ms  = self.trigger_timeout
        )
        
        log.info(" - Sample Interval    %s " % self.sample_interval)

        self.scope.setSamplingInterval(
            self.sample_interval,
            self.sample_duration
        )

        log.info(" - Sample Channel:    %s" % self.sample_channel)
        log.info(" - Sample Range:      +/-%d V" % self.sample_range)

        self.scope.setChannel(
            channel     = self.sample_channel,
            coupling    = self.sample_coupling,
            VRange      = self.sample_range
        )


    def CloseScope(self):
        """
        Close the scope connection
        """
        log.info("Closing scope connection")
        self.scope.close()
