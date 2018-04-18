
"""
File containing classes and functions for interfacing with the power
measurement scope.
"""

import os
import sys
import logging as log
import numpy as np

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
        self.trigger_threshold  = 1.0
        self.trigger_direction  = u'Rising'
        self.trigger_timeout    = 100

        self.no_of_captures     = 1
        self.no_of_samples      = None

        self.sample_channel     = "A"
        self.sample_range       = 10e-3
        self.sample_coupling    = "DC"
        self.sample_frequency   = 125e6
        self.sample_count       = 12500
        self.samples_per_segment= None
        
    def OpenScope(self):
        """
        Open a connection to a scope.
        """
        self.scope = ps5000a.PS5000a()
        log.info("Connected to scope:\n"+self.scope.getAllUnitInfo())

    def StartCapture(self):
        """
        Run a single capture cycle using the current scope configuration.
        Call this function, then WaitForReady in order to prime and then
        read captured data from the probe.
        """
        self.scope.runBlock()
        log.info("Running Scope Capture...")

    def WaitForReady(self):
        """
        Blocks until the probe is triggered.
        """
        log.info("Waiting for scope to be ready...")
        self.scope.waitReady()

    def GetData(self, channel):
        """
        Return the data captured in the previous block run.
        Block runs are initiated by StartCapture
        """
        log.info("Fetching Scope Data...")
        
        try:
            tr = self.scope.getDataV(channel, exceptOverflow=True)
            self.no_of_samples = self.scope.noSamples

            return tr
        except Exception as e:
            log.error("Channel %s" % channel)
            log.error(str(e))
            return [0]


    
    def ConfigureScope(self):
        """
        Used to write configuration of channels and triggers to the
        scope.
        """
        log.info("Configuring Scope...")
        
        log.info(" - Sample Count       %s " % self.sample_count)
        log.info(" - Sample Frequency   %s S/s" % self.sample_frequency)

        self.scope.setResolution('14')
        self.scope.setSamplingFrequency(
            self.sample_frequency,
            self.sample_count
        )

        log.info(" - Sample Channel:    %s" % self.sample_channel)
        log.info(" - Sample Range:      +/-%f V" % self.sample_range)

        self.scope.setChannel(
            channel     = self.sample_channel,
            coupling    = self.sample_coupling,
            VRange      = self.sample_range
        )
        
        self.scope.setChannel(
            channel     = self.trigger_channel,
            coupling    = self.sample_coupling,
            VRange      = 5
        )

        self.samples_per_segment = self.scope.memorySegments(
            self.no_of_captures
        )
        
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


    def CloseScope(self):
        """
        Close the scope connection
        """
        log.info("Closing scope connection")
        self.scope.close()
