#!/usr/bin/python3

"""

This script works as a testbench for the CPA attack built into the
acquisition framwork.

Requirements:
- You will need to have installed all of the requirements in the
  `requirements.txt` file using pip3.
- You will need to checkout the scale-data git repository found at
  https://github.com/danpage/scale-data
  including all of the Git Large File Storage (LFS) files which contain
  the traces.

Running this script:

- Assuming you have got the scale-data repository installed at ~/scale-data
- Run
    $> ./tests/test_CPA.py ~/scale-data/trace/<BOARD>/known
  Where <BOARD> is any one of the four boards supported.
- The script will load all of the trace files in the supplied folder, and
  run the CPA attack on them.
- The key value for the traces is `2B7E151628AED2A6ABF7158809CF4F3C`
- The attack is successful if this value is printed out at the end.

"""

import os
import sys
import gzip
import pickle

import numpy as np
import matplotlib.pyplot as plt

from tqdm import tqdm

cdir = os.path.dirname(__file__)
jdir = os.path.join(cdir,"../")
adir = os.path.abspath(jdir)
sys.path.insert(0, adir)

import sassrig as sr

def main():
    print("Testing CPA Attack")
    
    tracedir = sys.argv[1]

    print("Trace locations: %s" % tracedir)

    tracefiles = sorted([os.path.join(tracedir,f) 
        for f in os.listdir(tracedir) 
            if os.path.isfile(os.path.join(tracedir, f))])

    t_set = sr.SAFTraceSet()
    
    setup     = False
    trace_len = None
    pb        = tqdm(range(0, len(tracefiles)))

    for i in pb:

        tf = tracefiles[i]

        fd = gzip.open(tf,"rb")

        message = pickle.load(fd,encoding="latin1")
        cipher  = pickle.load(fd,encoding="latin1")
        trace   = pickle.load(fd,encoding="latin1")

        if(not setup):
            setup     = True
            trace_len = trace.shape[0]
            t_set.Allocate(len(tracefiles), trace_len, len(message))
            pb.set_description(
                "%d traces of length %d, with %d byte plaintexts."%
                (len(tracefiles),len(trace),len(message)))

        #print("%d, %s"%(i,str(trace.shape)))
        t_set._traces[i,0:trace_len]     = trace[0:trace_len]
        t_set._plaintexts[i,:] = message

        fd.close()

    print("Loaded %d traces of length %d" % 
        (t_set.num_traces,t_set.trace_length))

    print("Running CPA Attack...")

    attack = sr.SAFAttackCPA(None)
    attack.num_threads = 6
    R, guess = attack.run(t_set)

    print("Final Key Guess: %s" % (guess.hex()))


if(__name__ == "__main__"):
    main()
