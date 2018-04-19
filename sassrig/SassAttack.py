
"""
This file is used to attack traces we have captured using the flow
"""


import os
import sys
import logging as log

import numpy as np
import matplotlib.pyplot as plt
from progress.bar import ShadyBar as progressbar

from .SassStorage import SassStorage

class SassAttack:
    """
    Class containing everything we need to run an attack.
    """


    def __init__(self, args):
        """
        Create a new attack class.
        """
        self.args       = args
        self.tracefile  = args.trace_file

    def run(self):
        """
        Run the full attack
        """
        log.info("Running attack on trace file: %s" % self.tracefile)

        self.storage = SassStorage(self.tracefile)
        
        log.info("Loaded %d traces..." % len(self.storage))
