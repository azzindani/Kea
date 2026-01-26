from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def histogram(a: NumericData, bins: Union[int, str] = 10, range: Optional[List[float]] = None) -> Dict[str, Any]:
    """
    Compute the histogram of a data set.
    bins: 'auto', 'fd', 'doane', 'scott', 'stone', 'rice', 'sturges', 'sqrt' or int.
    """
    bin_arg = bins
    if isinstance(bins, str) and bins.isdigit():
        bin_arg = int(bins)
        
    hist, bin_edges = np.histogram(parse_array(a), bins=bin_arg, range=range)
    return to_serializable({
        "hist": hist.tolist(),
        "bin_edges": bin_edges.tolist()
    })

async def bincount(x: NumericData, minlength: int = 0) -> List[int]:
    """Count number of occurrences of each value in array of non-negative ints."""
    arr = parse_array(x, dtype='int64') # Must be int
    return to_serializable(np.bincount(arr, minlength=minlength).tolist())

async def digitize(x: NumericData, bins: List[float], right: bool = False) -> List[int]:
    """Return the indices of the bins to which each value in input array belongs."""
    return to_serializable(np.digitize(parse_array(x), bins, right=right).tolist())

async def correlate(a: NumericData, v: NumericData, mode: str = 'valid') -> List[float]:
    """Cross-correlation of two 1-dimensional sequences."""
    return to_serializable(np.correlate(parse_array(a), parse_array(v), mode=mode).tolist())

async def convolve(a: NumericData, v: NumericData, mode: str = 'full') -> List[float]:
    """Returns the discrete, linear convolution of two one-dimensional sequences."""
    return to_serializable(np.convolve(parse_array(a), parse_array(v), mode=mode).tolist())

async def cov(m: NumericData) -> List[List[float]]:
    """Estimate a covariance matrix, given data and weights."""
    return to_serializable(np.cov(parse_array(m)).tolist())
