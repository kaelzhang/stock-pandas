from cython import Py_ssize_t
from numpy cimport (
    ndarray,
    float64_t
)
import numpy as np

cimport numpy as cnp

cnp.import_array()

cdef:
    float64_t NaN = <float64_t>np.nan

# ----------------------------------------------------------------------
# Exponentially weighted moving average
# ported from pandas 1.0.0

def ewma(
    float64_t[:] vals,
    float64_t com,
    int adjust,
    bint ignore_na,
    int minp
):
    """
    Compute exponentially-weighted moving average using center-of-mass.
    Parameters
    ----------
    vals : ndarray (float64 type)
    com : float64
    adjust: int
    ignore_na: bool
    minp: int
    Returns
    -------
    ndarray
    """

    cdef:
        Py_ssize_t N = len(vals)
        ndarray[float64_t] output = np.empty(N, dtype=np.float64)
        float64_t alpha, old_wt_factor, new_wt, weighted_avg, old_wt, cur
        Py_ssize_t i, nobs
        bint is_observation

    if N == 0:
        return output

    minp = max(minp, 1)

    alpha = 1. / (1. + com)
    old_wt_factor = 1. - alpha
    new_wt = 1. if adjust else alpha

    weighted_avg = vals[0]
    is_observation = (weighted_avg == weighted_avg)
    nobs = int(is_observation)
    output[0] = weighted_avg if (nobs >= minp) else NaN
    old_wt = 1.

    with nogil:
        for i in range(1, N):
            cur = vals[i]
            is_observation = (cur == cur)
            nobs += is_observation
            if weighted_avg == weighted_avg:

                if is_observation or (not ignore_na):

                    old_wt *= old_wt_factor
                    if is_observation:

                        # avoid numerical errors on constant series
                        if weighted_avg != cur:
                            weighted_avg = ((old_wt * weighted_avg) +
                                            (new_wt * cur)) / (old_wt + new_wt)
                        if adjust:
                            old_wt += new_wt
                        else:
                            old_wt = 1.
            elif is_observation:
                weighted_avg = cur

            output[i] = weighted_avg if (nobs >= minp) else NaN

    return output
