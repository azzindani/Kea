from mcp_servers.numpy_server.tools.core_ops import to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

async def create_array(data: NumericData) -> List[Any]:
    """Create array from list/string."""
    # Already parsed via core logic if we were using it inside parsing, 
    # but here we just pass through to numpy and serialise
    arr = np.array(data)
    return to_serializable(arr.tolist())

async def create_zeros(shape: List[int]) -> List[Any]:
    """Create array of zeros."""
    return to_serializable(np.zeros(shape).tolist())

async def create_ones(shape: List[int]) -> List[Any]:
    """Create array of ones."""
    return to_serializable(np.ones(shape).tolist())

async def create_full(shape: List[int], fill_value: Union[float, int]) -> List[Any]:
    """Create array filled with constant."""
    return to_serializable(np.full(shape, fill_value).tolist())

async def arange(start: float, stop: float = None, step: float = 1) -> List[float]:
    """Return evenly spaced values within a given interval."""
    # Handle stop=None logic similar to np.arange(stop)
    if stop is None:
        stop = start
        start = 0
    return to_serializable(np.arange(start, stop, step).tolist())

async def linspace(start: float, stop: float, num: int = 50) -> List[float]:
    """Return evenly spaced numbers over a specified interval."""
    return to_serializable(np.linspace(start, stop, num).tolist())

async def logspace(start: float, stop: float, num: int = 50, base: float = 10.0) -> List[float]:
    """Return numbers spaced evenly on a log scale."""
    return to_serializable(np.logspace(start, stop, num, base=base).tolist())

async def geomspace(start: float, stop: float, num: int = 50) -> List[float]:
    """Return numbers spaced evenly on a geometric progression."""
    return to_serializable(np.geomspace(start, stop, num).tolist())

async def eye(N: int, M: Optional[int] = None, k: int = 0) -> List[List[float]]:
    """Return a 2-D array with ones on the diagonal and zeros elsewhere."""
    return to_serializable(np.eye(N, M, k=k).tolist())

async def identity(n: int) -> List[List[float]]:
    """Return the identity array."""
    return to_serializable(np.identity(n).tolist())

async def diag(v: NumericData, k: int = 0) -> List[Any]:
    """Extract diagonal or construct diagonal array."""
    # If 1D constructs 2D, if 2D extracts 1D
    # core_ops parsing isn't strictly needed if we just pass list to np.array
    # but let's be safe
    arr = np.array(v) if isinstance(v, list) else np.array(v) 
    # v can be list of list for 2D
    return to_serializable(np.diag(arr, k=k).tolist())

async def vander(x: List[float], N: Optional[int] = None) -> List[List[float]]:
    """Generate a Vandermonde matrix."""
    return to_serializable(np.vander(x, N).tolist())
