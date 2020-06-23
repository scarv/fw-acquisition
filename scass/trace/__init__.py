
import lz4.frame
import gzip
import numpy as np
import logging as log

from .TraceWriterBase   import TraceWriterBase
from .TraceReaderBase   import TraceReaderBase
from .TraceWriterSimple import TraceWriterSimple
from .TraceReaderSimple import TraceReaderSimple
from .TraceSet          import TraceSet
from .TraceCapture      import TraceCapture


def saveTracesToDisk(filepath, traces):
    
    assert(isinstance(traces,np.ndarray))

    if(filepath.endswith(".gz")):

        with gzip.GzipFile(filepath,"w") as gzfh:
            np.save(file=gzfh, arr=traces)

    elif(filepath.endswith(".lz4")):

        with lzf.frame.open(filepath,mode="wb") as lzfh:
            np.save(file=lzfh, arr=traces)

    elif(filepath.endswith(".npy")):
        
        np.save(filepath, traces)

    else:
        log.error("Unknown file extension: '%s'" % filepath)
        log.error("Could not save traces to disk.")
        raise Exception("Unknown file extension: '%s'" % filepath)

    log.info("Saved traces to '%s'" % filepath)


def loadTracesFromDisk(filepath):

    data = None

    log.info("Loading traces from '%s'" % filepath)
    
    if(filepath.endswith(".gz")):

        with gzip.GzipFile(filepath,"r") as gzfh:
            data = np.load(gzfh)

    elif(filepath.endswith(".lz4")):

        with lzf.frame.open(filepath,mode="r") as lzfh:
            data = np.load(lzfh)

    elif(filepath.endswith(".npy")):
        
        data = np.load(filepath)

    else:
        log.error("Unknown file extension: '%s'" % filepath)
        log.error("Could not load traces from disk.")
        raise Exception("Unknown file extension: '%s'" % filepath)

    return data
