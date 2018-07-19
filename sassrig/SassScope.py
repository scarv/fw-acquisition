#!/usr/bin/python3

"""
File containing classes and functions for interfacing with the power
measurement scope.
"""

import os
import sys
import array
import logging as log
import numpy as np
import argparse
import matplotlib.pyplot as plt

from picoscope import ps5000a

if(__name__=="__main__"):
    from SassComms import SassComms
else:
    from .SassComms import SassComms


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
        self.sample_count       = 11000
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
            tr = self.scope.getDataV(channel, exceptOverflow=False)
            tr = array.array("f", tr)
            self.no_of_samples = self.scope.noSamples

            return tr
        except Exception as e:
            #log.error("Channel %s" % channel)
            #log.error(str(e))
            return [None,e]

    
    def FindBestSampleRate(self,comms,cpu_freq,graph=False,
        trigger_threshold = 0.5):
        """
        Tries to find the best sample rate to include the entire
        AES process. Returns the number of samples which should be
        captured to get the entire operation being anaylsed.
        """
        resolution  = '8'
        sample_freq = 2 * cpu_freq
        
        self.scope.setResolution(resolution)
        
        sample_count = 1000
        finished     = False

        plt.ion()

        while(not finished):
            actualSampleFreq, maxSamples = \
                self.scope.setSamplingFrequency(sample_freq,sample_count)
            
            self.sample_frequency = actualSampleFreq
            self.sample_count     = sample_count

            self.StartCapture()
            comms.doEncrypt()
            self.WaitForReady()
            power   = self.GetData("A")
            trigger = self.GetData("B")
            
            trigger = trigger / np.max(trigger)
            idx1    = trigger[:] >  trigger_threshold
            idx0    = trigger[:] <= trigger_threshold
            trigger[idx1] = 1.0
            trigger[idx0] = 0.0

            if(trigger[-1] == 1.0):
                finished = False
                sample_count += 1000
            else:
                finished = True

            if(graph):
                plt.figure(1)
                plt.clf()
                plt.subplot(2,1,1)
                plt.plot(power,linewidth=0.25)
                plt.subplot(2,1,2)
                plt.plot(trigger,linewidth=0.25)
                plt.show()
                plt.draw()
                plt.pause(0.001)

        plt.clf()
        plt.close()
        return sample_count

    def ConfigureTrigger(self, channel, threshold, direction, timeout):
        """
        Configure the supplied channel as a trigger signal for the scope.

        :param str channel:
        :param float threshold:
        :param str direction: Must be "Rising" or "Falling"
        :param float timeout: Timeout in miliseconds waiting for a trigger.
        """
        self.scope.setSimpleTrigger(
            channel,
            threshold,
            direction,
            timeout
        )
        

    def ConfigureChannel(self, channel, vrange, coupling):
        """
        Configure a single channel with the specified coupling and
        voltage range.
        
        :param str channel:
        :param float vrange: +- voltage range of this channel
        :param str coupling: "AC" or "DC"
        """
        self.scope.setChannel(
            channel     = channel,
            coupling    = coupling,
            VRange      = vrange
        )

    
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
        
        self.ConfigureTrigger(
            self.trigger_channel,
            self.trigger_threshold,
            self.trigger_direction,
            self.trigger_timeout
        )


    def CloseScope(self):
        """
        Close the scope connection
        """
        log.info("Closing scope connection")
        self.scope.close()


def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("port", type=str,
        help="Target serial port to use")
    parser.add_argument("baud", type=int,
        help="Baud rate for the serial port.")
    
    parser.add_argument("--freq", type=float,default=100e6,
        help="Working frequency of the CPU")
    
    parser.add_argument("--graph", action="store_true",
        help="Show graphs as we work")

    args = parser.parse_args()

    comms = SassComms(serialPort=args.port,serialBaud=args.baud)
    scope = SassScope()
    scope.OpenScope()
    scope.ConfigureScope()
    samplecount = scope.FindBestSampleRate(comms,args.freq,graph=args.graph)
    scope.CloseScope()
    comms.ClosePort()

    print("Sample count for CPU at %fHz is %d" % (args.freq,samplecount))

if(__name__ == "__main__"):
    main()


