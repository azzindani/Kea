from mcp_servers.numpy_server.tools.core_ops import parse_array, to_serializable, NumericData
import numpy as np
from typing import Dict, Any, List, Optional, Union

# Using new Generator API
rng = np.random.default_rng()

async def rand_float(size: Optional[List[int]] = None) -> List[Any]:
    """Random floats in [0, 1)."""
    return to_serializable(rng.random(size).tolist())

async def rand_int(low: int, high: Optional[int] = None, size: Optional[List[int]] = None) -> List[Any]:
    """Random integers."""
    return to_serializable(rng.integers(low, high, size=size).tolist())

async def rand_normal(loc: float = 0.0, scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]:
    """Draw samples from a normal distribution."""
    return to_serializable(rng.normal(loc, scale, size).tolist())

async def rand_uniform(low: float = 0.0, high: float = 1.0, size: Optional[List[int]] = None) -> List[Any]:
    """Draw samples from a uniform distribution."""
    return to_serializable(rng.uniform(low, high, size).tolist())

async def rand_choice(a: NumericData, size: Optional[List[int]] = None, replace: bool = True, p: Optional[NumericData] = None) -> List[Any]:
    """Generates a random sample from a given 1-D array."""
    arr = parse_array(a)
    p_arr = parse_array(p) if p is not None else None
    return to_serializable(rng.choice(arr, size=size, replace=replace, p=p_arr).tolist())

async def shuffle(x: NumericData) -> List[Any]:
    """Modify a sequence in-place by shuffling its contents."""
    arr = parse_array(x).copy() # Copy to simulate immutable inputs, return new
    rng.shuffle(arr)
    return to_serializable(arr.tolist())

async def permutation(x: Union[int, NumericData]) -> List[Any]:
    """Randomly permute a sequence, or return a permuted range."""
    if isinstance(x, int):
        target = x
    else:
        target = parse_array(x)
    return to_serializable(rng.permutation(target).tolist())

# Distributions
async def rand_beta(a: float, b: float, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.beta(a, b, size).tolist())

async def rand_binomial(n: int, p: float, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.binomial(n, p, size).tolist())

async def rand_chisquare(df: float, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.chisquare(df, size).tolist())

async def rand_gamma(shape: float, scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.gamma(shape, scale, size).tolist())

async def rand_poisson(lam: float = 1.0, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.poisson(lam, size).tolist())

async def rand_exponential(scale: float = 1.0, size: Optional[List[int]] = None) -> List[Any]:
    return to_serializable(rng.exponential(scale, size).tolist())
