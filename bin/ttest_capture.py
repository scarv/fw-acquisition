#!/usr/bin/python3

"""
A tool script for capturing TTest data sets
"""

import os
import sys
import argparse
import logging as log
import time

scass_path = os.path.expandvars(
    os.path.join(os.path.dirname(__file__),"../")
)
sys.path.append(scass_path)

import scass

def parse_args():
    """
    Parse command line arguments to the script
    """
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-n","--num-traces",type=int,
        help="Number of traces to capture in total",default=10000)
    
    parser.add_argument("-b","--baud",type=int,
        help="Baud rate to communicate with target at",default=9600)
    
    parser.add_argument("-k","--keep-data",action="store_true",
        help="Store input data with the captured traces")
    
    parser.add_argument("-l", "--logfile", type=str,default=None,
        help="Log TTest information and progress to this file.)")
    
    parser.add_argument("--zero-fixed",action="store_true",
        help="Tie all TTest fixed values to zero")

    parser.add_argument("--set-vars", type=str, nargs="+",
        help="Set an input variable/parameter of the experiment to this value"
        )

    parser.add_argument("target",type=str,
        help="TTY port to connect too when communicating with the target")
    
    parser.add_argument("scope",type=str,
        help="Scope configuration file")
    
    parser.add_argument("power_channel",type=str,
        help="Scope Channel ID which samples the power signal")
    
    parser.add_argument("trs_prefix",type=str,
        help="File path prefix from which artifact file names are generated.")
    

    return parser

def main(argparser,ttest_class = scass.ttest.TTestCapture):
    """
    Main function for the tool script
    parameters:
    argparser  - instance of argparse.ArgumentParser
    ttest_class - ttest capture class, must be an
            instanceof(scass.ttest.TTestCapture)
    """
    args    = argparser.parse_args()

    if(args.logfile != None):
        log.basicConfig(filename=args.logfile, filemode="w",level=log.DEBUG)
    else:
        log.basicConfig(level=log.DEBUG)
    log.getLogger().addHandler(log.StreamHandler())

    log.info("Connecting to %s @ %d"%(args.target,args.baud))

    target  = scass.comms.Target(args.target,args.baud)

    try:
        assert(target.doHelloWorld()),"Failed target hello world handshake"
    except Exception as e:
        print(e)
        return 1

    experiment_name = target.doGetExperiementName()

    log.info("Experiment Name    : '%s'" % experiment_name)

    log.info("Scope Configuration: %s" % args.scope)
    scope           = scass.scope.fromConfig(args.scope)

    log.info("- Max Samples     : %d" % scope.max_samples)
    log.info("- Num Samples     : %d" % scope.num_samples)
    log.info("- Sample Frequency: %fHz" % scope.sample_freq)
    log.info("- Resolution      : %s" % str(scope.resolution))
    log.info("- Trigger Channel : %s" % scope.trigger_channel.channel_id)
    log.info("- Signal  Channel : %s" % args.power_channel)

    log.info("Initialise experiment...")

    try:
        assert(target.doInitExperiment()),"Failed target experiment init"
    except Exception as e:
        print(e)
        return 2

    log.info("Try single trace capture...")

    scope.runCapture()
    target.doRunFixedExperiment()

    while(scope.scopeReady() == False):
        pass

    power_channel = scope.getChannel(args.power_channel)

    sig_trigger = scope.getRawChannelData(
        scope.trigger_channel, scope.max_samples)
    sig_power   = scope.getRawChannelData(
        power_channel,scope.max_samples)

    log.info("Finding trigger window size...")
    window_size = 0
    retries     = 0
    while(window_size <= 10 and retries < 10):
        log.info("- Attempt %d" % retries)
        window_size = scope.findTriggerWindowSize(sig_trigger)
        retries += 1
        time.sleep(1)

    if(window_size <= 10):
        log.error("Failed to find window size after 10 attempts.")
        return 1

    log.info("Trigger Window Size: %d" % window_size)
    log.info("Trace Datatype     : %s" % str(sig_power.dtype))

    log.info("Experiment Cycles : %d" % target.doGetExperimentCycles())
    log.info("Experiment InstRet: %d" % target.doGetExperimentInstrRet())
    
    log.info("Random Bytes      : %d" % target.doRandGetLen())
    log.info("Randomness Rate   : %d" % target.doRandGetRefreshRate())

    ttest       = ttest_class(
        target,
        scope,
        scope.trigger_channel,
        power_channel,
        args.trs_prefix,
        num_traces = args.num_traces,
        num_samples = window_size
    )

    if(args.zero_fixed):
        ttest.zeros_as_fixed_value = True

    log.info("Initialising TTest Capture...")

    ttest.initialiseTTest()

    if(args.set_vars == None):
        pass

    else:

        for varset in args.set_vars:
            varname,value = varset.split("=")

            log.info("Setting input variable %s = %s" % (varname, value))
            value_int = int(value)

            var = ttest.getVariableByName(varname)
            value_bytes = value_int.to_bytes(var.size, byteorder="little")

            var.setFixedValue(value_bytes)
            var.takeFixedValue()

            # Variables have their values sent to the target device
            # by the TTestCapture class, _assign_ttest_fixed_values
            # function.


    ttest.reportVariables()

    log.info("Running TTest Capture...")

    ttest.performTTest()

    log.info("TTest Capture Finished")

    log.info("Finished Successfully")

    return 0


if(__name__ == "__main__"):

    argparser = parse_args()

    sys.exit(
        main(
            argparser,
            scass.ttest.TTestCapture
        )
    )

