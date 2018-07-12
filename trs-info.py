#!/usr/bin/python3

"""
A script for printing information in a trace file.
"""

import os
import sys
import argparse
import configparser
import logging as log

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

import sassrig


tpath = sys.argv[1]
tfile = sassrig.SassStorage(trs_file = tpath, info_only = True)

print("%s" % tpath)
print("Number of traces     : %d" % tfile.num_traces)
print("Length of trace      : %d" % tfile.samples_per_trace)
print("Length of plaintext  : %d" % tfile.data_per_trace)
print("Data Encoding        : %d" % int.from_bytes(tfile.coding_type,"little"))
print("Trace Description    : ")
print("\t", tfile.trace_description.replace("\n","\n\t"))
