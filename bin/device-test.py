#!/usr/bin/python3

"""
A script for checking that a target device can be properly controlled
using the SCASS Framework.
Also acts as a simple demonstration of how to communicate with the
target devices via SCASS
"""

import os
import sys
import secrets
import argparse
import logging as log

import serial

scass_path = os.path.expandvars(
    os.path.join(os.path.dirname(__file__),"../")
)
sys.path.append(scass_path)

import scass

def build_arg_parser():
    """
    Parse command line arguments to the script.
    """
    
    parser = argparse.ArgumentParser()

    parser.add_argument("-b","--baud",type=int,default=9600,
        help="Baud rate to communicate with target at. Default=9600")
    
    parser.add_argument("port",type=str,
        help="TTY port to connect too when communicating with the target")
    
    return parser


def main(argparser):
    """
    Script main function
    """
    args = argparser.parse_args()
    
    log.info("Connecting to target %s@%d" % (args.port, args.baud))

    target = scass.comms.Target(args.port,args.baud)

    log.info("Doing hello world...")
    assert(target.doHelloWorld())

    log.info("Getting experiment name...")
    ename = target.doGetExperiementName()
    log.info("> Experiment name: '%s'" % (ename))


    log.info("Getting number of experiment variables...")
    evar_count = target.doGetVarNum()
    log.info("> Experiment variable count: %d" % (evar_count))


    log.info("Enumerating variables...")
    log.info("%20s | %5s | %8s" %("Name", "Size","Flags"))
    log.info("-"*40)


    for i in range(0,evar_count):
        vname, vsize, vflags = target.doGetVarInfo(i)

        new_value = secrets.token_bytes(vsize)

        target.doSetVarValue(i, new_value)

        set_value = target.doGetVarValue(i, vsize)

        assert(new_value == set_value),\
            "Setting value of %s. Expected %s, got %s" % (
                vname,new_value,set_value)

        log.info("%20s | %5d | 0x%08x" % (vname, vsize, vflags))


    log.info("Getting randomness array size..")
    rand_size = target.doRandGetLen()
    log.info("> Random array size: %d" % rand_size)
    log.info("Seeding random data array...")
    target.doRandSeed(secrets.token_bytes(rand_size))

    log.info("Initialising experimnet...")
    target.doInitExperiment()

    ntimes = 10
    log.info("Running experiment %d times..." % (ntimes))
    for i in range(0,10):
        log.info("> %d / %d" % (i,ntimes))
        target.doRunExperiment()


    log.info("Getting instruction count...")
    eicount = target.doGetExperimentInstrRet()
    log.info("Getting cycle count...")
    eccount = target.doGetExperimentCycles()
    log.info("> Instructions: %d" % eicount)
    log.info("> Cycles      : %d" % eccount)


    log.info("--- Finish ---")



if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    main(build_arg_parser())

