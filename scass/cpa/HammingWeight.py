
import numpy as np

def hw(x):
    """Return hamming weight of x"""
    c = 0
    if(isinstance(x,np.ndarray)):
        for y in x:
            z = y
            while z > 0:
                c  = c + 1
                z &= z-1
    else:
        while x > 0:
            c  = c + 1
            x &= x-1
    return c

def hammingWeightCorrolation(traces,inputs):
    """
    Compute the hamming weight corrolation trace from the given trace
    set and input values.

    traces - an np.NdArray where each row is a single trace.
    inputs - an np.NdArray where each i'th element is the input for each
             i'th trace row.
    """
    
    D_trace_count, T_trace_len  = traces.shape

    # Key guesses are always one here, since we take values directly from
    # the input arrays.
    K_guesses                   = 1

    T = traces

    H = np.zeros((D_trace_count, K_guesses))

    for i in range(0, D_trace_count):
        H[i,0] = hw(inputs[i])

    H_avgs = np.mean(H,axis=0)
    T_avgs = np.mean(T,axis=0)

    R = np.zeros((K_guesses, T_trace_len))

    for i in range(0,K_guesses):

        H_avg   = H_avgs[i]
        H_col   = H[:,i]
        H_col_d = H_col - H_avg
    
        H_col_sq_sum = np.dot(H_col_d,H_col_d)

        for j in range(0, T_trace_len):

            T_avg   = T_avgs[j]
            T_col   = traces[:D_trace_count,j]
            T_col_d = T_col - T_avg
            T_col_sq_sum = np.dot(T_col_d, T_col_d)

            top = np.dot(H_col_d, T_col_d)

            bot = np.sqrt(H_col_sq_sum * T_col_sq_sum)
            if(bot == 0):
                bot = 1

            R[i,j] = np.abs(top/bot)
    
    return R.transpose()
