#!/usr/bin/python3

"""
A tool script for capturing trace data sets
"""

import os
import sys
import argparse
import logging as log

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
    
    parser.add_argument("target",type=str,
        help="TTY port to connect too when communicating with the target")
    
    parser.add_argument("scope",type=str,
        help="Scope configuration file")
    
    parser.add_argument("power_channel",type=str,
        help="Scope Channel ID which samples the power signal")
    
    parser.add_argument("trs_set",type=argparse.FileType("wb"),
        help="File path to store fixed data trace set")

    return parser

def main(argparser,capture_class = scass.trace.TraceCapture):
    """
    Main function for the tool script
    parameters:
    argparser  - instance of argparse.ArgumentParser
    capture_class - trace capture class, must be an
            instanceof(scass.trace.TraceCapture)
    """
    args    = argparser.parse_args()

    if(args.logfile != None):
        log.basicConfig(filename=args.logfile, filemode="w",level=log.DEBUG)
    else:
        log.basicConfig(level=log.DEBUG)

    log.info("Connecting to %s @ %d"%(args.target,args.baud))

    target  = scass.comms.Target(args.target,args.baud)

    try:
        assert(target.doHelloWorld()),"Failed target hello world handshake"
    except Exception as e:
        print(e)
        return 1

    experiment_name = target.doGetExperiementName()

    log.info("Experiment Name    : '%s'" % experiment_name)

    input_data_len  = target.doGetInputDataLength()
    output_data_len = target.doGetOutputDataLength()

    log.info("Input Data Length  : %d" % input_data_len)
    log.info("Output Data Length : %d" % output_data_len)

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
    target.doRunExperiment()

    while(scope.scopeReady() == False):
        pass
    
    power_channel = scope.getChannel(args.power_channel)

    sig_trigger = scope.getRawChannelData(
        scope.trigger_channel, scope.max_samples)
    sig_power   = scope.getRawChannelData(
        power_channel,scope.max_samples)

    log.info("Finding trigger window size...")
    window_size = scope.findTriggerWindowSize(sig_trigger)

    log.info("Trigger Window Size: %d" % window_size)
    log.info("Trace Datatype     : %s" % str(sig_power.dtype))

    trace_set = scass.trace.TraceWriterSimple(
        args.trs_set, sig_power.dtype)

    capture = capture_class(
        target,
        scope,
        scope.trigger_channel,
        power_channel,
        trace_set,
        num_traces = args.num_traces,
        num_samples = window_size
    )

    log.info("Keep Input Data: %s" % str(args.keep_data))
    capture.store_input_with_trace = args.keep_data

    prepared = capture.prepareCapture()
    
    if(not prepared):
        return 1

    log.info("Running Trace Capture...")

    capture.runCapture()
    
    log.info("TTest Capture Finished")
    log.info("Traces Captured   : %d" % trace_set.traces_written)

    trace_set.close()

    log.info("Finished Successfully")

    return 0


if(__name__ == "__main__"):

    argparser = parse_args()

    sys.exit(
        main(
            argparser,
            scass.trace.TraceCapture
        )
    )


