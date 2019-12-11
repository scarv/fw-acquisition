#!/usr/bin/python3

"""
A script for doing very simple plotting
"""

import os
import sys
import secrets
import argparse
import logging as log

import gzip
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

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

    parser.add_argument("-t","--title",type=str,help="Graph plot title")

    parser.add_argument("--layout",type=str,
        choices=["overlap","rows"],
        default = "overlap",
        help="How to layout all of the plots.")

    parser.add_argument("--width",type=float, default=10.5,
        help="Width of the graph.")
    
    parser.add_argument("--height",type=float, default=3.5,
        help="Height of the graph.")

    parser.add_argument("--ymax",type=float,
        help="Fix maximum value of Y axis")
    
    parser.add_argument("--critical-value",type=float,
        help="Critical value for TTest threshold")

    parser.add_argument("--abs",action="store_true",
        help="Plot the absolute value of the input traces.")

    parser.add_argument("graph",type=str,
        help="File to save the plot too.")
    
    parser.add_argument("inputs",type=str,nargs="+",
        help="The input traces to plot")
    
    return parser

def main(argparser):
    """
    Script main function
    """
    args = argparser.parse_args()

    num_inputs = len(args.inputs)

    # Overlap all plots on one graph, or show as columns?
    rows = num_inputs
    if(args.layout == "rows"):
        rows = 1

    fig, axs  = plt.subplots(rows,1)
    
    fig.set_size_inches(args.width,args.height,forward=True)

    if(isinstance(axs, matplotlib.axes.Axes)):
        axs = [axs]

    row = 0

    for intrace in args.inputs:

        trace = np.load(intrace)

        if(args.abs):
            trace = np.abs(trace)

        if(args.ymax):
            axs[row].set_ylim(top = args.ymax)

        axs[row].plot(trace, linewidth=0.1)

        if(args.layout ==" rows"):
            row += 1

        if(not args.layout == "overlap"):
            axs[row].set_title(os.path.basename(intrace))


    if(args.critical_value):
        plt.plot(
            [args.critical_value]*trace.size,
            linewidth=0.25,color="red"
        )

        if(not args.abs):

            plt.plot(
                [-args.critical_value]*trace.size,
                linewidth=0.25,color="red"
            )

    # Plot main title.
    if(args.title):
        fig.suptitle(args.title)

    plt.tight_layout()
    plt.savefig(args.graph,bbox_inches="tight",pad_inches=0)


if(__name__ == "__main__"):
    log.basicConfig(level=log.INFO)
    ap = build_arg_parser()
    sys.exit(main(ap))
